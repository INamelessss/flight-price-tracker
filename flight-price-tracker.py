from unidecode import unidecode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import tkinter as tk
from tkinter import ttk
from openpyxl import Workbook
import matplotlib.pyplot as plt

class FlightPriceTracker:
    def __init__(self):
        self.destinos = [
            "Arequipa", "Ayacucho", "Cajamarca", "Chiclayo", "Cusco", "Ilo", "Iquitos",
            "Jauja", "Jaén", "Juliaca", "Lima", "Piura", "Pucallpa", "Puerto Maldonado",
            "Tacna", "Talara", "Tarapoto", "Trujillo", "Tumbes"
        ]
        self.driver = webdriver.Chrome()
        self.driver.get("https://www.latamairlines.com/pe/es/destinos/sudamerica")
        self.root = tk.Tk()
        self.root.title("Seleccionar Lugar de Partida")
        self.combo_var = tk.StringVar()
        self.combo = ttk.Combobox(self.root, textvariable=self.combo_var)
        self.combo['values'] = self.destinos
        self.combo.bind("<<ComboboxSelected>>", self.seleccionar_lugar_partida)
        self.combo.pack()

    def cargar_mas_ofertas(self):
        try:
            boton_mostrar_mas = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'btnPagging'))
            )
            boton_mostrar_mas.click()
            return True
        except:
            return False

    def guardar_datos_en_excel(self, lugar_partida, destino_list, usd_prices, pen_prices):
        wb = Workbook()
        ws = wb.active

        ws.append(["Destino", "PEN Price", "USD Price"])

        for destino, pen_price, usd_price in zip(destino_list, pen_prices, usd_prices):
            ws.append([destino, pen_price, usd_price])

        excel_filename = f'{lugar_partida}_flight_prices.xlsx'
        wb.save(excel_filename)
        print(f'Datos guardados en: {excel_filename}')
        self.analizar_datos(lugar_partida)
        self.root.destroy()

    def analizar_datos(self, lugar_partida):
        excel_filename = f'{lugar_partida}_flight_prices.xlsx'
        df = pd.read_excel(excel_filename)

        df['PEN Price'] = pd.to_numeric(df['PEN Price'].str.replace(',', ''), errors='coerce')

        plt.figure(figsize=(10, 6))
        plt.bar(df['Destino'], df['PEN Price'], color='blue')
        plt.xlabel('Destino')
        plt.ylabel('Precio en PEN')
        plt.title('Precios de vuelos por destino en PEN')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.show()

        destino_mas_caro = df.loc[df['PEN Price'].idxmax()]
        destino_mas_barato = df.loc[df['PEN Price'].idxmin()]

        print(f"Destino más caro: {destino_mas_caro['Destino']} - PEN Price: {destino_mas_caro['PEN Price']}")
        print(f"Destino más barato: {destino_mas_barato['Destino']} - PEN Price: {destino_mas_barato['PEN Price']}")

        umbral_precio = 1000  # Definir umbral de precio
        destinos_baratos = df[df['PEN Price'] < umbral_precio]

        if destinos_baratos.empty:
            print(f"No hay destinos por debajo del umbral de {umbral_precio} PEN.")
        else:
            print("Destinos con precios por debajo del umbral:")
            print(destinos_baratos)

    def seleccionar_lugar_partida(self, event):
        lugar_partida = self.combo_var.get()

        self.combo['state'] = 'disabled'

        origin_button = self.driver.find_element(By.ID, "originSelector")
        origin_button.click()

        wait = WebDriverWait(self.driver, 10)
        origin_popup = wait.until(EC.presence_of_element_located((By.ID, "originSelector-popup")))

        origin_option = origin_popup.find_element(By.XPATH, f"//p[contains(text(), '{lugar_partida}')]")
        origin_option.click()

        while self.cargar_mas_ofertas():
            time.sleep(5)

        html = self.driver.page_source

        soup = BeautifulSoup(html, 'html.parser')

        flight_data = soup.find_all('div', class_='middle-text')

        destino_list = [unidecode(destino.text.strip()) for destino in flight_data]

        flight_prices = soup.find_all('div', class_='amount')

        usd_prices = []
        pen_prices = []
        usd_pen_prices = []

        for price in flight_prices:
            price_text = price.get_text().replace('Â', '')
            usd_pen_prices.append(price_text.replace('USD', '').strip())

        for price in usd_pen_prices:
            usd, pen = price.split('PEN\xa0')
            usd_prices.append(usd)
            pen_prices.append(pen)

        self.guardar_datos_en_excel(lugar_partida, destino_list, usd_prices, pen_prices)

        self.driver.quit()
        self.root.mainloop()

if __name__ == "__main__":
    tracker = FlightPriceTracker()
