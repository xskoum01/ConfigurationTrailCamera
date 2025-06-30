import time

from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget, QPushButton, QMessageBox, QComboBox, QInputDialog
from PyQt6.QtWidgets import QMainWindow, QCheckBox, QGraphicsScene, QGraphicsView, QLineEdit
from PyQt6 import uic
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtCore import QTimer
import serial
import serial.tools.list_ports
import re
import json  # Přidáme modul pro zpracování JSON

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        uic.loadUi("./gui/MainWindow.ui", self)

        self.resize(1182, 826)  # Změňte hodnoty na požadovanou velikost

        # set up statusbar
        self.status_db = QWidget()
        self.status_db_layout = QHBoxLayout()
        self.status_db_layout.setSpacing(0)
        self.status_db.setLayout(self.status_db_layout)
        self.statusBar().addPermanentWidget(self.status_db)
        self.statusBar()

        # lookup for a button exit
        self.exit_action = self.findChild(QAction, "actionExit")
        self.exit_action.triggered.connect(self.close)

        # window display show
        self.show()

        # Inicializace sériového připojení a časovače
        self.serial_connection = None
        self.serial_timer = QTimer(self)

        # Načtení prvků z GUI pomocí findChild
        self.portComboBox = self.findChild(QComboBox, "portComboBox")
        self.connectButton = self.findChild(QPushButton, "connect_butt")
        self.refreshButton = self.findChild(QPushButton, "refreshButton")
        self.statusLabel = self.findChild(QLabel, "statusLabel")
        self.phoneNumberComboBox = self.findChild(QComboBox, "phoneNumberComboBox")
        self.camRstButton = self.findChild(QPushButton, "camRstButt")
        self.lteRstButton = self.findChild(QPushButton, "lteRstButt")
        self.wakeupComboBox = self.findChild(QComboBox, "wakeupcomboBox")
        self.sendPhotoComboBox = self.findChild(QComboBox, "sendPhotoComboBox")
        self.resolutionComboBox = self.findChild(QComboBox, "resolutioncomboBox")
        self.qualitycomboBox = self.findChild(QComboBox, "qualitycomboBox")
        self.addPhoneNum = self.findChild(QPushButton, "addPhoneNum")
        self.batteryCheckBox = self.findChild(QCheckBox, "batterycheckBox")
        self.chargingCheckBox = self.findChild(QCheckBox, "chargingcheckBox")
        self.batterylifeCheckBox = self.findChild(QCheckBox, "batterykifecheckBox")
        self.sendAutoSMScheckBox = self.findChild(QCheckBox, "sendAutoSMScheckBox")
        #self.sendPhotosCheckBox = self.findChild(QCheckBox, "sendPhotosCheckBox")
        self.sendSMSPushButton = self.findChild(QPushButton, "sendSMSpushButton")
        self.photoView = self.findChild(QGraphicsView, "photoView")
        self.takePhotoButton = self.findChild(QPushButton, "takephotopushButton")
        self.getBatteryButton = self.findChild(QPushButton, "getbatterypushButton")
        self.getChargingButton = self.findChild(QPushButton, "getchargingpushButton")
        self.getRemainingTimeButton = self.findChild(QPushButton, "gettimepushButton")
        self.defaultConfButt = self.findChild(QPushButton, "defaultConfButt")
        self.saveConfButton = self.findChild(QPushButton, "saveConfButton")
        self.getSingalLevelButton = self.findChild(QPushButton, "getSingalLevelButton")
        self.batteryLabel = self.findChild(QLabel, "batterylabel")
        self.chargingLabel = self.findChild(QLabel, "charginglabel")
        self.remainingTimeLabel = self.findChild(QLabel, "remaininglabel")
        self.signalLevellabel = self.findChild(QLabel, "signalLevellabel")
        self.apnLineEdit = self.findChild(QLineEdit, "apnLineEdit")
        self.urlLineEdit = self.findChild(QLineEdit, "urlLineEdit")
        self.sharedKeyLineEdit = self.findChild(QLineEdit, "sharedKeyLineEdit")

        # Přidáme přednastavené prvky ComboBoxu
        self.wakeupComboBox.addItems(["30 s", "60 s", "5 min", "10 min", "30 min", "60 min", "5 h",
                                      "24 h", "48 h"])
        self.sendPhotoComboBox.addItems(["Immediately", "After 1 hour", "After 3 hours"])
        self.resolutionComboBox.addItems([
            "320x240 (QVGA)",
            "640x480 (VGA)",
            "800x600 (SVGA)",
            "1024x768 (XGA)",
            "1280x720 (HD)",
            "1600x1200 (UXGA)"
        ])
        self.phoneNumberComboBox.addItem("+420735009345")
        self.qualitycomboBox.addItems([
         "Very high",
         "High",
         "Middle",
         "Low"
        ])

        # Připojíme událost změny výběru k metodě pro zpracování
        self.sendPhotoComboBox.currentIndexChanged.connect(self.set_sendPhoto)
        self.resolutionComboBox.currentIndexChanged.connect(self.set_resolution)
        self.wakeupComboBox.currentIndexChanged.connect(self.set_wakeUpTime)
        self.qualitycomboBox.currentIndexChanged.connect(self.set_qualityPhoto)

        # Přiřadíme funkce k tlačítkům
        self.connectButton.clicked.connect(self.connect_to_port)
        self.refreshButton.clicked.connect(self.refresh_ports)
        self.addPhoneNum.clicked.connect(self.add_phone_number)
        self.sendSMSPushButton.clicked.connect(self.send_sms)
        self.takePhotoButton.clicked.connect(self.request_photo_from_esp32)
        self.getBatteryButton.clicked.connect(self.get_battery_level)
        self.getChargingButton.clicked.connect(self.get_charging_status)
        self.getRemainingTimeButton.clicked.connect(self.get_remaining_time)
        self.camRstButton.clicked.connect(self.trailCamReset)
        self.lteRstButton.clicked.connect(self.lteReset)
        self.defaultConfButt.clicked.connect(self.reset_to_default)
        self.saveConfButton.clicked.connect(self.save_configuration)
        self.getSingalLevelButton.clicked.connect(self.get_signalLevel)

        # V konstruktoru __init__ připojte každý CheckBox k funkci check_checkbox_status
        self.batteryCheckBox.stateChanged.connect(self.check_checkbox_status)
        self.chargingCheckBox.stateChanged.connect(self.check_checkbox_status)
        self.batterylifeCheckBox.stateChanged.connect(self.check_checkbox_status)
        self.sendAutoSMScheckBox.stateChanged.connect(self.checkbox_sendSMS_status)
        #self.sendPhotosCheckBox.stateChanged.connect(self.checkbox_sendPhotosToURL)

        self.scene = QGraphicsScene(self)
        self.photoView.setScene(self.scene)

        # Načteme dostupné porty při spuštění aplikace
        self.refresh_ports()
        self.serial_buffer = ""  # Inicializace bufferu pro příjem sériových dat

    def trailCamReset(self):
        # Odešleme restartovací příkaz
        self.send_command_to_esp32("RESTART")

        # Zavřeme sériové připojení (protože ESP32 se restartuje, UART spojení je přerušeno)
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.serial_connection = None

        # Vyčistíme GUI status
        self.statusBar().showMessage("🔄 Trail Camera restarting. Please reconnect.")

    def lteReset(self):
        response = self.send_command_to_esp32("RESTARTLTE")
        if response == "LTERESTARTED":
            self.statusBar().showMessage("✅ LTE module was restarted.")

    def get_battery_level(self):
        response = self.send_command_to_esp32("GET_BATTERY_LEVEL")
        if response:
            self.batteryLabel.setText(response)
            self.statusBar().showMessage("✅ Battery level updated.")

    def get_charging_status(self):
        response = self.send_command_to_esp32("GET_CHARGING_STATUS")
        if response:
            self.chargingLabel.setText(response)
            self.statusBar().showMessage("✅ Charging status updated.")

    def get_remaining_time(self):
        response = self.send_command_to_esp32("GET_REMAINING_TIME")
        if response:
            self.remainingTimeLabel.setText(response)
            self.statusBar().showMessage("✅ Remaining battery time updated.")

    def get_signalLevel(self):
        response = self.send_command_to_esp32("GET_SIGNAL")
        if response:
            self.signalLevellabel.setText(response)
            self.statusBar().showMessage("✅ Signal Level updated.")

    def closeEvent(self, event):
        # Ujistěte se, že sériové připojení je zavřené při zavření aplikace
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write(b"EXIT_CONFIG\n")
            self.serial_connection.close()
        event.accept()

    def request_photo_from_esp32(self):
        """ Požádá ESP32 o snímek, přijme jej a zobrazí v aplikaci. """

        # 1️⃣ Nejprve zkontrolujeme, zda jsme připojeni k ESP32
        if not self.serial_connection or not self.serial_connection.is_open:
            QMessageBox.warning(self, "Connection Error", "ESP32 is not connected.")
            return

        try:
            # 2️⃣ Pokud již je v náhledovém okně nějaká fotka, smažeme ji
            if not self.scene.items():  # Pokud není prázdná
                self.scene.clear()  # Odstranění starého obrázku

            self.serial_connection.reset_input_buffer()  # Vyčistíme buffer

            # 3️⃣ Odeslání příkazu k pořízení snímku
            self.serial_connection.write(b'TAKE_PHOTO\n')
            self.statusBar().showMessage("📡 Požadavek na snímek odeslán...")
            time.sleep(0.5)

            # 4️⃣ Čekáme na odpověď s metadaty
            while True:
                response = self.serial_connection.readline().decode().strip()
                if response.startswith("{") and response.endswith("}"):  # Ověření JSON formátu
                    break  # Máme validní JSON, pokračujeme

            # 5️⃣ Ověření JSON odpovědi (velikost souboru)
            try:
                photo_data = json.loads(response)
                photo_size = int(photo_data.get("PHOTO_SIZE", 0))
                if photo_size <= 0:
                    self.statusBar().showMessage("⚠️ Neplatná velikost fotky.")
                    return
            except json.JSONDecodeError:
                self.statusBar().showMessage(f"⚠️ Neplatný JSON při čtení fotky: {response}")
                return

            # 6️⃣ Načítání binárních dat
            received_bytes = 0
            with open("received_photo.jpg", "wb") as file:
                while received_bytes < photo_size:
                    data = self.serial_connection.read(min(1024, photo_size - received_bytes))
                    if not data:
                        break
                    file.write(data)
                    received_bytes += len(data)

            # 7️⃣ Kontrola správnosti přenosu
            if received_bytes == photo_size:
                self.statusBar().showMessage("✅ Photo OK.")
                self.display_photo("received_photo.jpg")  # Zobrazení nové fotky
            else:
                self.statusBar().showMessage(f"⚠️ Photo err ({received_bytes}/{photo_size} bytes).")

        except serial.SerialException as e:
            QMessageBox.critical(self, "Serial Error", f"⚠️ Chyba komunikace se zařízením: {e}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"⚠️ Neočekávaná chyba při přijímání fotografie: {e}")

    def display_photo(self, file_path):
        # Načítání a zobrazení fotografie
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            QMessageBox.critical(self, "Error", "Failed to load the image.")
            return

        self.scene.clear()
        pixmap_item = self.scene.addPixmap(pixmap)
        rect = QRectF(pixmap.rect())
        self.photoView.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def send_sms(self):
        if not self.serial_connection or not self.serial_connection.is_open:
            QMessageBox.warning(self, "Connection Error", "ESP32 is not connected.")
            return

        phone_number = self.phoneNumberComboBox.currentText()

        if not phone_number:
            QMessageBox.warning(self, "Missing Phone Number", "Please select a phone number.")
            return

        flags = ""
        if self.batteryCheckBox.isChecked():
            flags += "B"
        if self.chargingCheckBox.isChecked():
            flags += "C"
        if self.batterylifeCheckBox.isChecked():
            flags += "T"

        if not flags:
            QMessageBox.warning(self, "Empty Message", "Please select at least one message option.")
            return

        try:
            # Nepoužíváme nové otevření portu – využijeme self.serial_connection
            command = f"SEND_SMS:{phone_number}:{flags}\n"
            self.serial_connection.write(command.encode())
            self.serial_connection.flush()

            self.statusBar().showMessage(f"📤 SMS command sent to {phone_number} with flags: {flags}")

        except serial.SerialException as e:
            QMessageBox.critical(self, "Serial Communication Error", f"❌ Failed to send SMS: {e}")

    def checkbox_sendSMS_status(self):
        send_sms_when_captured = self.sendAutoSMScheckBox.isChecked()
        status_message = "Auto SMS active " if send_sms_when_captured else "Auto SMS inactive"
        self.statusBar().showMessage(status_message)

    def check_checkbox_status(self):
        battery_checked = self.batteryCheckBox.isChecked()
        charging_checked = self.chargingCheckBox.isChecked()
        batterylife_checked = self.batterylifeCheckBox.isChecked()

        status_message = "Status - "
        status_message += "Battery: ON, " if battery_checked else "Battery: OFF, "
        status_message += "Charging: ON, " if charging_checked else "Charging: OFF, "
        status_message += "Battery Life: ON" if batterylife_checked else "Battery Life: OFF"

        self.statusBar().showMessage(status_message)

    def add_phone_number(self):
        """ Otevře dialogové okno pro zadání telefonního čísla a přidá ho do ComboBoxu """
        phone_number, ok = QInputDialog.getText(
            self,
            "Write Phone Number",
            "Write phone number in format: +420XXXXXXXXX"
        )

        if ok and phone_number:  # Uživatel potvrdil vstup
            # Ověření, zda číslo odpovídá formátu +420XXXXXXXXX
            if re.fullmatch(r"\+420\d{9}", phone_number):
                # Zkontrolujeme, jestli číslo není již v ComboBoxu
                if phone_number not in [self.phoneNumberComboBox.itemText(i) for i in
                                        range(self.phoneNumberComboBox.count())]:
                    # Přidáme nové číslo do ComboBoxu
                    self.phoneNumberComboBox.addItem(phone_number)
                    self.statusBar().showMessage(f"📞 Phone number {phone_number} added.")
                else:
                    QMessageBox.warning(self, "Duplicate Number", "This phone number is already in the list.")
            else:
                QMessageBox.warning(self, "Invalid Format", "Phone number must be in the format +420XXXXXXXXX.")


    def set_qualityPhoto(self):
        selected_quality = self.qualitycomboBox.currentText()
        self.statusBar().showMessage(f"Quality of Photo set: {selected_quality}")

    def set_wakeUpTime(self):
        selected_wakeUpTime = self.wakeupComboBox.currentText()
        self.statusBar().showMessage(f"Wake up time set: {selected_wakeUpTime}")

    def set_sendPhoto(self):
        selected_sendPhoto = self.sendPhotoComboBox.currentText()
        self.statusBar().showMessage(f"Send Photo set to: {selected_sendPhoto}")

    def set_resolution(self):
        selected_resolution = self.resolutionComboBox.currentText()
        self.statusBar().showMessage(f"Photo resolution set: {selected_resolution}")

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()

        self.portComboBox.clear()

        for port in ports:
            self.portComboBox.addItem(port.device)

        if self.portComboBox.count() == 0:
            self.statusBar().showMessage("❌ No ports available")
        else:
            self.statusBar().showMessage("Choose port")

    def send_command_to_esp32(self, command):
        if not self.serial_connection or not self.serial_connection.is_open:
            QMessageBox.warning(self, "Connection Error", "ESP32 is not connected.")
            return None

        try:
            self.serial_connection.reset_input_buffer()  # 🧹 VYČISTÍME BUFFER
            time.sleep(0.05)  # Volitelně malá prodleva – může pomoci

            self.serial_connection.write((command + "\n").encode())
            self.serial_connection.flush()

            if command == "RESTART":
                self.statusBar().showMessage("✅ Trail Camera was restarted.")
                return None

            # 🕒 Čekáme na odpověď max. 1 sekundu
            start = time.time()
            response = ""
            while time.time() - start < 3.0:
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode().strip()
                    break

            return response if response else None

        except serial.SerialException as e:
            self.statusBar().showMessage(f"❌ Communication error: {e}")
            return None

    def connect_to_port(self):
        """ Připojení k ESP32, poslání WAKEUP a načtení JSON konfigurace """
        selected_port = self.portComboBox.currentText()

        if not selected_port:
            self.statusBar().showMessage("Choose port")
            return

        try:
            # ✅ Zavřeme staré připojení, pokud existuje
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()

            # ✅ Otevřeme nové sériové připojení
            self.serial_connection = serial.Serial(selected_port, 115200, timeout=1)
            self.statusBar().showMessage(f"Connected to {selected_port}")

            # ✅ Vyčistíme buffer, abychom ignorovali bootovací zprávy ESP32
            self.serial_connection.reset_input_buffer()
            time.sleep(1)  # Dáme ESP32 čas na inicializaci

            # ✅ Pošleme WAKEUP, aby se ESP32 probudilo
            self.serial_connection.write(b"WAKEUP\n")
            self.serial_connection.flush()
            self.statusBar().showMessage("📡 WAKEUP odeslán, čekáme na konfiguraci...")

            # ✅ Čekáme maximálně 1 sekundu na validní JSON odpověď
            start_time = time.time()
            response = ""

            while time.time() - start_time < 1:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode(errors='ignore').strip()
                    print(f"📡 Přijatá data: {line}")  # Debug výpis

                    if line.startswith("{") and line.endswith("}"):  # Ověření JSON formátu
                        response = line
                        break  # Jakmile máme validní JSON, nemusíme číst dál

            # ✅ Ověření, zda jsme dostali validní JSON
            if not response.startswith("{") or not response.endswith("}"):
                self.statusBar().showMessage("⚠️ Not Connected.")
                if self.serial_connection and self.serial_connection.is_open:
                    self.serial_connection.close()
                return

            # ✅ Zpracování JSON odpovědi a aktualizace GUI
            try:
                config_data = json.loads(response)
                print(f"✅ Loaded configuration: {config_data}")  # Debug JSON

                self.wakeupComboBox.setCurrentText(config_data.get("wakeup_time", ""))

                # 🛠️ Převod "send_photo" číselné hodnoty na text pro GUI
                send_photo_value = config_data.get("send_photo", "0")
                if send_photo_value == "0":
                    self.sendPhotoComboBox.setCurrentText("Immediately")
                elif send_photo_value == "1":
                    self.sendPhotoComboBox.setCurrentText("After 1 hour")
                elif send_photo_value == "2":
                    self.sendPhotoComboBox.setCurrentText("After 3 hours")
                else:
                    self.sendPhotoComboBox.setCurrentText("Immediately")  # Fallback

                resolution = config_data.get("resolution")
                if resolution == "320x240 (QVGA)":
                    self.resolutionComboBox.setCurrentText("320x240 (QVGA)")
                elif resolution == "640x480 (VGA)":
                    self.resolutionComboBox.setCurrentText("640x480 (VGA)")
                elif resolution == "800x600 (SVGA)":
                    self.resolutionComboBox.setCurrentText("800x600 (SVGA)")
                elif resolution == "1024x768 (XGA)":
                    self.resolutionComboBox.setCurrentText("1024x768 (XGA)")
                elif resolution == "1280x720 (HD)":
                    self.resolutionComboBox.setCurrentText("1280x720 (HD)")
                elif resolution == "1600x1200 (UXGA)":
                    self.resolutionComboBox.setCurrentText("1600x1200 (UXGA)")

                self.qualitycomboBox.setCurrentText(config_data.get("quality", ""))
                self.phoneNumberComboBox.setCurrentText(config_data.get("phone_number", ""))
                self.apnLineEdit.setText(config_data.get("apn", ""))
                self.urlLineEdit.setText(config_data.get("url", ""))
                self.sharedKeyLineEdit.setText(config_data.get("shared_key", ""))

                # ✅ Ověření, zda je hodnota bool, pokud ano, převést na string
                send_sms = str(config_data.get("send_sms", "false")).lower()

                # ✅ Nastavení checkboxů
                #self.sendPhotosCheckBox.setChecked(send_photo == "true")
                self.sendAutoSMScheckBox.setChecked(send_sms == "true")

                self.statusBar().showMessage("✅ Configuration of TrailCamera loaded.")

            except json.JSONDecodeError:
                self.statusBar().showMessage("⚠️ Decoding JSON error")

        except serial.SerialException as e:
            QMessageBox.critical(self, "Serial Error", f"⚠️ Communication err: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"⚠️ Unexpected err: {e}")

    def reset_to_default(self):
        """ Reset konfigurace na výchozí hodnoty a načtení nové konfigurace """
        if not self.serial_connection or not self.serial_connection.is_open:
            QMessageBox.warning(self, "Connection Error", "ESP32 is not connected.")
            return

        try:
            # ✅ Pošleme příkaz RESET_CONFIG
            self.serial_connection.write(b"RESET_CONFIG\n")
            self.serial_connection.flush()
            self.statusBar().showMessage("📡 Reset, waiting for default configuration.")

            # ✅ Čekáme maximálně 1 sekundu na validní JSON odpověď
            start_time = time.time()
            response = ""

            while time.time() - start_time < 1:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode(errors='ignore').strip()
                    print(f"📡 Received serial data: {line}")  # Debug výpis

                    if line.startswith("{") and line.endswith("}"):
                        response = line
                        break

            if not response.startswith("{") or not response.endswith("}"):
                self.statusBar().showMessage("⚠️ Bad configuration (timeout).")
                return

            # ✅ Zpracování JSON odpovědi a aktualizace GUI
            try:
                config_data = json.loads(response)
                print(f"✅ Loaded data after reset: {config_data}")  # Debug JSON

                self.wakeupComboBox.setCurrentText(config_data.get("wakeup_time", ""))

                # 🔄 Mapování send_photo hodnoty
                send_photo_value = config_data.get("send_photo", "0")
                if send_photo_value == "0":
                    self.sendPhotoComboBox.setCurrentText("Immediately")
                elif send_photo_value == "1":
                    self.sendPhotoComboBox.setCurrentText("After 1 hour")
                elif send_photo_value == "2":
                    self.sendPhotoComboBox.setCurrentText("After 3 hours")
                else:
                    self.sendPhotoComboBox.setCurrentText("Immediately")

                # 🔄 Resolution (použij rovnou pokud je ve formátu "1024x768 (XGA)")
                resolution = config_data.get("resolution", "")
                self.resolutionComboBox.setCurrentText(resolution)

                # 🔄 Quality – pokud náhodou přijde ve špatném formátu, ošetříme fallback
                quality = config_data.get("quality", "")
                if quality in ["Very high", "High", "Medium", "Low"]:
                    self.qualitycomboBox.setCurrentText(quality)
                else:
                    self.qualitycomboBox.setCurrentIndex(1)  # defaultně "High"

                self.phoneNumberComboBox.setCurrentText(config_data.get("phone_number", ""))
                self.apnLineEdit.setText(config_data.get("apn", ""))
                self.urlLineEdit.setText(config_data.get("url", ""))
                self.sharedKeyLineEdit.setText(config_data.get("shared_key", ""))

                # ✅ Checkboxy
                send_sms = str(config_data.get("send_sms", "false")).lower()
                self.sendAutoSMScheckBox.setChecked(send_sms == "true")

                self.batteryLabel.setText(config_data.get("send_battery", ""))
                self.chargingLabel.setText(config_data.get("send_charging", ""))
                self.remainingTimeLabel.setText(config_data.get("send_time_remaining", ""))

                self.statusBar().showMessage("✅ Configuration reset!")

            except json.JSONDecodeError as e:
                print(f"❌ Chyba při parsování JSON: {e}")
                self.statusBar().showMessage(f"⚠️ Neplatný JSON po resetu: {response}")

        except serial.SerialException as e:
            QMessageBox.critical(self, "Serial Error", f"⚠️ Communication Error: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"⚠️ Unexpected Error: {e}")

    def save_configuration(self):
        """ Uloží aktuální konfiguraci do ESP32 přes sériovou linku """
        if not self.serial_connection or not self.serial_connection.is_open:
            QMessageBox.warning(self, "Connection Error", "ESP32 is not connected.")
            return

        # 📥 Převod send_photo podle výběru v GUI
        send_photo_text = self.sendPhotoComboBox.currentText()
        if send_photo_text == "Immediately":
            send_photo_value = "0"
        elif send_photo_text == "After 1 hour":
            send_photo_value = "1"
        elif send_photo_text == "After 3 hours":
            send_photo_value = "2"
        else:
            send_photo_value = "0"  # Výchozí fallback, pokud by tam bylo něco jiného

        # 📋 Sestavení JSON objektu z GUI prvků
        config_data = {
            "wakeup_time": self.wakeupComboBox.currentText(),
            "send_photo": send_photo_value,
            "resolution": self.resolutionComboBox.currentText(),
            "quality": self.qualitycomboBox.currentText(),
            "phone_number": self.phoneNumberComboBox.currentText(),
            "apn": self.apnLineEdit.text(),
            "url": self.urlLineEdit.text(),
            "shared_key": self.sharedKeyLineEdit.text(),
            "send_sms": "true" if self.sendAutoSMScheckBox.isChecked() else "false",
            #"send_photo": "true" if self.sendPhotosCheckBox.isChecked() else "false"
        }

        # 📡 Serializace JSON a odeslání přes sériovou linku
        try:
            json_config = json.dumps(config_data)
            print(f"SET_CONFIG:{json_config}\n".encode())

            # Odeslání konfigurace
            self.serial_connection.write(f"SET_CONFIG:{json_config}\n".encode())
            self.serial_connection.flush()
            self.statusBar().showMessage("📡 Configuration sent to ESP32.")

            # ⏳ Čekáme na odpověď od ESP32
            time.sleep(0.5)
            if self.serial_connection.in_waiting:
                response = self.serial_connection.readline().decode().strip()
                if response == "OK":
                    self.statusBar().showMessage("✅ Configuration saved.")
                else:
                    self.statusBar().showMessage(f"⚠️ ESP32 answer: {response}")

        except Exception as e:
            QMessageBox.critical(self, "Serial Error", f"❌ serial error: {e}")















