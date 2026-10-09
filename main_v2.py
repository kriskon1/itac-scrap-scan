import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import requests
from datetime import datetime
import re


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()

        self.session_id = None
        self.pers_id = None
        self.locale = None
        self.current_user = ""
        self.log_count = 0

        # Google Form beállítások
        self.GF_FORM_ID = "xxxxxx"
        self.GF_USER_ID = "1701880874"
        self.GF_ENTRY_SERIAL_ID = "262317029"
        self.GF_PRODUCT = "104131889"
        self.GF_LINE_ID = "1564880645"
        self.GF_LAST_STATION_ID = "1961048156"
        self.GF_FAIL_STATION_ID = "78982433"
        self.GF_FAIL_TIME_ID = "456943472"
        self.GF_FAILURE_TYPE_DESC = "1543173779"
        self.GF_FAILURE_INFO = "694785822"
        self.GF_FAILURE_HISTORY = "961651466"
        self.GF_ALIGNMENT_ID = "831574698"

        self.show_login_screen()

    def show_login_screen(self):
        self.login_window = tk.Toplevel(self.root)
        self.login_window.title("Bejelentkezés")
        self.login_window.geometry("380x220")
        self.login_window.resizable(False, False)

        frame = tk.Frame(self.login_window, padx=20, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text="Felhasználónév:", font=("Segoe UI", 12)).grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.user_entry = tk.Entry(frame, font=("Segoe UI", 12), width=18)
        self.user_entry.grid(row=0, column=1, pady=5)

        tk.Label(frame, text="Jelszó:", font=("Segoe UI", 12)).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.pass_entry = tk.Entry(frame, font=("Segoe UI", 12), width=18, show="*")
        self.pass_entry.grid(row=1, column=1, pady=5)

        login_btn = tk.Button(frame, text="Bejelentkezés", font=("Segoe UI", 12, "bold"),
                              bg="#008000", fg="white", command=self.do_login)
        login_btn.grid(row=2, column=0, columnspan=2, pady=15, ipadx=10, ipady=3)

        self.login_window.bind('<Return>', lambda event: self.do_login())
        self.user_entry.focus()

    def do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get().strip()

        if not username or not password:
            return

        if self.perform_login(username, password):
            self.current_user = username
            self.login_window.destroy()
            self.show_main_menu()
        else:
            messagebox.showerror("Hiba", "Bejelentkezés sikertelen.", parent=self.login_window)

    def perform_login(self, username, password):
        url = "http://10.207.63.180:8080/mes/imsapi/rest/actions/regLogin"
        payload = {
            "sessionValidationStruct": {
                "stationNumber": "",
                "stationPassword": "",
                "user": username,
                "password": password,
                "client": "01",
                "registrationType": "U",
                "systemIdentifier": "http://10.207.63.180:8080"
            }
        }
        try:
            resp = requests.post(url, json=payload, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                ctx = data.get("result", {}).get("sessionContext", {})
                self.session_id = str(ctx.get("sessionId", "-1"))
                self.pers_id = str(ctx.get("persId", ""))
                self.locale = str(ctx.get("locale", ""))
                return self.session_id != "-1"
            return False
        except Exception as e:
            print(f"Login hiba: {e}")
            return False

    def show_main_menu(self):
        self.root.deiconify()
        self.root.title(f"Szériaszám Feltöltő - Bejelentkezve: {self.current_user}")
        self.root.geometry("1310x420")
        self.root.minsize(1310, 420)

        top_frame = tk.Frame(self.root, padx=10, pady=10)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        tk.Label(top_frame, text="Szériaszám:", font=("Segoe UI", 12)).pack(side=tk.LEFT, padx=(0, 5))
        self.serial_entry = tk.Entry(top_frame, font=("Segoe UI", 16))
        self.serial_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.serial_entry.bind('<Return>', lambda event: self.process_serial())

        center_frame = tk.Frame(self.root, padx=10, pady=10)
        center_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        log_frame = tk.LabelFrame(center_frame, text="Eredmények", font=("Segoe UI", 10))
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.log_area = ScrolledText(log_frame, font=("Consolas", 11), wrap=tk.WORD, height=10)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_area.config(state=tk.DISABLED)

        self.serial_entry.focus()

    def append_log(self, text):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def process_serial(self):
        serial = self.serial_entry.get().strip()
        if not serial:
            messagebox.showwarning("Figyelmeztetés", "Add meg a szériaszámot!")
            return

        # 1. Lekérjük a history-t
        history_data = self.trGetSerialNumberHistoryData(serial)

        part_number = history_data.get("result", {}).get("partNumber", "Ismeretlen")
        values = history_data.get("result", {}).get("bookingResultValues", [])

        # --- ÚJ: Hiba részletek kinyerése (CSAK AZ UTOLSÓ) ---
        failure_values = history_data.get("result", {}).get("failureDataResultValues", [])
        fail_type_desc = "-"
        fail_info = "-"

        if len(failure_values) >= 2:
            # Szigorúan csak a legutolsó hiba adatait vesszük ki (a tömb utolsó 2 eleme)
            fail_type_desc = str(failure_values[-2])
            fail_info = str(failure_values[-1])
        # ----------------------------------------------------

        failures = []
        alignment_station = "Ismeretlen"
        line_name = "Ismeretlen"

        # Ebbe a változóba fogjuk menteni az utolsó állomás nevét, függetlenül a státusztól
        last_history_station_desc = "-"

        # 2. Adatok kinyerése
        for i in range(0, len(values) - 3, 4):
            st_num = str(values[i])
            ts_str = str(values[i + 1])
            st_desc = str(values[i + 2])
            state = str(values[i + 3])

            # Minden iterációban felülírjuk, így a ciklus végén az utolsó állomás neve lesz benne
            last_history_station_desc = st_desc

            if "AAC" in st_desc.upper():
                alignment_station = st_desc

            # Gyártósor kinyerése (pl. VES1-GEN603) minden VES1 sorból
            if st_num.startswith("VES1-GEN6"):
                parts = st_num.split("-")
                if len(parts) >= 2:
                    line_name = f"{parts[0]}-{parts[1]}"

            if st_num.startswith("VES1-GEN6") and state == "1":
                try:
                    ts_sec = int(ts_str) / 1000.0
                    dt = datetime.fromtimestamp(ts_sec)
                    formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    formatted_time = "Ismeretlen időpont"

                failures.append({"code": st_num, "desc": st_desc, "time": formatted_time})
        last_history_station_desc = re.sub(r'\s+L\d+$', '', last_history_station_desc, flags=re.IGNORECASE).strip()

        # 3. KÜLDÉS ELŐKÉSZÍTÉSE ÉS MES SCRAP
        all_failures_text = ""
        last_failure_desc = "PASS (Nincs hiba)"
        last_failure_time = "-"
        scrap_status_text = ""

        if len(failures) == 0:
            all_failures_text = "PASS (Nincs hiba)"
            fail_type_desc = "-"
            fail_info = "-"
        else:
            last_failure = failures[-1]
            last_station_code = last_failure["code"]
            last_failure_time = last_failure["time"]

            # LEVÁGJUK AZ L1, L2, L3 stb. VÉGZŐDÉST A Regex segítségével
            last_failure_desc = re.sub(r'\s+L\d+$', '', last_failure["desc"], flags=re.IGNORECASE).strip()

            # Ha van hiba, összerakjuk a listát
            for i, f in enumerate(failures, 1):
                all_failures_text += f"{i}. {f['desc']} (Idő: {f['time']})\n"

            all_failures_text = all_failures_text.strip()

            # # MES API hívása a Scrap státusz beállítására az utolsó állomással
            # mes_resp = self.trUploadState(last_station_code, serial)
            # if self.is_return_value_zero(mes_resp):
            #     scrap_status_text = " [MES: Scrap OK]"
            # else:
            #     scrap_status_text = " [MES: Scrap Hiba]"

        # 4. KÜLDÉS A GOOGLE FORM-BA
        self.log_count += 1

        # Átadjuk az új változókat is
        success = self.log_to_google_form(serial, part_number, line_name, alignment_station, last_failure_desc,
                                          last_failure_time, all_failures_text, fail_type_desc, fail_info,
                                          last_history_station_desc)

        # 5. Felület frissítése
        if success:
            hibak_szama = len(failures)
            if hibak_szama > 0:
                log_szoveg = f"{self.log_count}. [{serial}] | Aktuális állomás: {last_history_station_desc} | Sor: {line_name} | AA: {alignment_station} | Bukások: {hibak_szama} db (Utolsó: {last_failure_desc}){scrap_status_text}"
            else:
                log_szoveg = f"{self.log_count}. [{serial}] | Aktuális állomás: {last_history_station_desc} | Sor: {line_name} | AA: {alignment_station} | Bukások: 0 db (PASS)"

            self.append_log(log_szoveg)
        else:
            self.append_log(f"{self.log_count}. Hálózati hiba a feltöltésnél: [{serial}]")

        self.serial_entry.delete(0, tk.END)
        self.serial_entry.focus()

    def is_return_value_zero(self, raw_data):
        try:
            return raw_data.get("result", {}).get("return_value", -1) == 0
        except Exception:
            return False

    def log_to_google_form(self, serial, part_number, line_name, alignment_station, last_fail_desc, last_fail_time,
                           all_failures_text, fail_type_desc, fail_info, last_history_station_desc):
        url = f"https://docs.google.com/forms/d/e/{self.GF_FORM_ID}/formResponse"

        # Bővítjük a payload-ot az új mezőkkel
        data = {
            f"entry.{self.GF_ENTRY_SERIAL_ID}": serial,
            f"entry.{self.GF_USER_ID}": self.current_user,
            f"entry.{self.GF_PRODUCT}": part_number,
            f"entry.{self.GF_LINE_ID}": line_name,
            f"entry.{self.GF_LAST_STATION_ID}": last_history_station_desc,
            f"entry.{self.GF_ALIGNMENT_ID}": alignment_station,
            f"entry.{self.GF_FAIL_STATION_ID}": last_fail_desc,
            f"entry.{self.GF_FAIL_TIME_ID}": last_fail_time,
            f"entry.{self.GF_FAILURE_HISTORY}": all_failures_text,
            f"entry.{self.GF_FAILURE_TYPE_DESC}": fail_type_desc,
            f"entry.{self.GF_FAILURE_INFO}": fail_info
        }

        try:
            resp = requests.post(url, data=data, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            print(f"Google Form log hiba: {e}")
            return False

    def trGetSerialNumberHistoryData(self, serial):
        url = "http://10.207.63.180:8080/mes/imsapi/rest/actions/trGetSerialNumberHistoryData"
        payload = {
            "sessionContext": {
                "sessionId": self.session_id,
                "persId": self.pers_id,
                "locale": self.locale
            },
            "stationNumber": "VES1-GEN601-130-01",
            "serialNumber": serial,
            "serialNumberPos": "",
            "processLayer": 2,
            "desolvingSerialNumber": 2,
            "desolvingLevel": 0,
            "bookingResultKeys": ["STATION_NUMBER", "BOOK_DATE", "STATION_DESC", "BOOK_STATE"],
            "failureDataResultKeys": ["FAILURE_TYPE_DESC", "INFO"]
        }
        try:
            resp = requests.post(url, json=payload, timeout=5)
            return resp.json() if resp.status_code == 200 else {}
        except Exception:
            return {}

    def trUploadState(self, station_number, serial):
        url = "http://10.207.63.180:8080/mes/imsapi/rest/actions/trUploadState"
        payload = {
            "sessionContext": {
                "sessionId": self.session_id,
                "persId": self.pers_id,
                "locale": self.locale
            },
            "stationNumber": station_number,
            "processLayer": 2,
            "serialNumberRef": serial,
            "serialNumberRefPos": -1,
            "serialNumberState": 2,
            "duplicateSerialNumber": 0,
            "bookDate": -1,
            "cycleTime": 1,
            "serialNumberUploadKeys": ["ERROR_CODE", "SERIAL_NUMBER", "SERIAL_NUMBER_STATE"],
            "serialNumberUploadValues": [0, serial, 0]
        }
        try:
            resp = requests.post(url, json=payload, timeout=5)
            return resp.json() if resp.status_code == 200 else {"result": {"return_value": -1}}
        except Exception:
            return {"result": {"return_value": -1}}


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
