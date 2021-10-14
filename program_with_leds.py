from cryptography.fernet import Fernet
from location_encrypt import encrypt
from location_encrypt import mapping
from pathlib import Path
import RPi.GPIO as GPIO
import time
import threading
import configparser
import inquirer
import serial
import pyotp
import pynmea2
import os

latitude = 0.00
longitude = 0.00
speed_over_ground = 0.00
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
led_red = 23
led_yellow = 24
led_green = 25
GPIO.setup(led_red, GPIO.OUT)
GPIO.setup(led_yellow, GPIO.OUT)
GPIO.setup(led_green, GPIO.OUT)

encrypted_key_file_path = "/home/shares/pi/enrypted_key.txt"
config_path = "/home/shares/pi/config.ini"

def save_config(config):
    with open(config_path, "w") as configfile:
        config.write(configfile)

def check_2fa(otp, totp):
    if otp == int(totp.now()):
        return True

def get_gps_data(gps_event, serial_connection):
    while gps_event.is_set():
        global latitude
        global longitude
        global speed_over_ground
        dataout = pynmea2.NMEAStreamReader()
        try:
            newdata=serial_connection.readline().decode('utf-8')
        except:
            break
        if newdata[0:6] == "$GPRMC":
            newmsg=pynmea2.parse(newdata)
            speed_over_ground = newmsg.data[6]
            latitude=newmsg.latitude
            longitude=newmsg.longitude

def input_gps_coordinates():
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    while True:
        try:
            input_longtitude = float(input("destination longtitude: "))
            if input_longtitude < 180 and input_longtitude > -180:
                break
        except ValueError:
            print("Error")
    while True:
        try:
            input_latitude = float(input("destination latitude: "))
            if input_latitude < 90 and input_latitude > -90:
                break
        except ValueError:
            print("Error")
    config["coordinates"]["lat_2"] = str(input_latitude)
    config["coordinates"]["lng_2"] = str(input_longtitude)
    with open(config_path, "w") as configfile:
        config.write(configfile)
        print("new coordinates saved")

# print(config["default"]["filename"])

def encryption_process():
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    filename = config["default"]["filename"]
    
    port=config["serial"]["port"]
    
    totp = pyotp.TOTP(config["sys"]["OTP"])
    #TODO: Hash the data
    data_hash, salt = encrypt.hash(encrypt.open_file(filename))
    config["encryption"]["data_hash"] = data_hash
    config["encryption"]["salt"] = salt
    save_config(config)
    #TODO: Hash the config
    config_data_hash, config_salt = encrypt.hash(encrypt.open_file(filename))
    config["encryption"]["config_data_hash"] = config_data_hash
    config["encryption"]["config_salt"] = config_salt
    save_config(config)
    # print(encrypt.check_hash(encrypt.open_file(filename), salt))

    #TODO: encypt the plaintext with the symetric key (key_s)
    symmetric_key, symmetric_key_raw = encrypt.generate_symmetric_key()
    encrypt.symmetric_encrypt(filename, symmetric_key)
    config["encryption"]["symmetric_key"] = str(symmetric_key_raw)
    save_config(config)

    #backwards
    # symmetric_key_raw = config["encryption"]["symmetric_key"]
    # symmetric_key = Fernet(symmetric_key_raw)
    # encrypt.symmetric_decrypt(filename, symmetric_key)

    #! ps position -> location mapping -> generate public key (key_e)
    #Check if Keys are already generated
    key_files = Path("keys/public_key.pem")
    if not key_files.is_file():
        encrypt.generate_rsa_keys()


    #TODO: ncypt symetric key (key_s) with public key (key_e)
    # encrypt the config with symetric key
    encrypt_ini = encrypt.symmetric_encrypt(config_path, symmetric_key)


    # encrypt symetric key (key_e) with public key (key_e)
    encrypted = encrypt.encrypt_rsa(symmetric_key_raw.encode())
    encrypt.save_encrypted_file(encrypted_key_file_path, encrypted)
    


#----------------------------------------------------------------
# zip all what you need
#send
# unzip evenything
#----------------------------------------------------------------

def decryption_process():
    file_data = encrypt.open_file(encrypted_key_file_path)
    #TODO: decrypt key_s with private key (key_d)
    decrypted = encrypt.decrypt_rsa(file_data)
    symmetric_key_raw = decrypted
    symmetric_key = Fernet(symmetric_key_raw)
    decrypt_ini = encrypt.symmetric_decrypt(config_path, symmetric_key)
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    filename = config["default"]["filename"]
    
    port=config["serial"]["port"]
    serial_connection=serial.Serial(port, baudrate=9600, timeout=0.5)
    totp = pyotp.TOTP(config["sys"]["OTP"])

    #!  gps position -> location mapping -> 
    ##Decrypt
    gps_event = threading.Event()
    gps_event.set()
    gps_thread = threading.Thread(target=get_gps_data, args=[gps_event, serial_connection])
    gps_thread.start()
    lat_2 = float(config["coordinates"]["lat_2"])
    lng_2 = float(config["coordinates"]["lng_2"])
    radius = float(config["default"]["radius"])     # 0.02 bedeutet auf 20 Meter

    try:
        while True:
            print("Latitude:  " + str(latitude))
            print("Longitude: " + str(longitude))
            status, difference = mapping.am_i_in_the_area(lat_2, lng_2, latitude, longitude, radius)
            if status:
                if check_2fa(int(input("OTP: ")), totp):  
                    encrypt.symmetric_decrypt(filename, symmetric_key)
                    print("in radius - file is decrypted")
                    GPIO.output(led_red, GPIO.LOW)
                    GPIO.output(led_yellow, GPIO.LOW)
                    GPIO.output(led_green, GPIO.HIGH)
                    os.remove(encrypted_key_file_path)
                    data_hash = config["encryption"]["data_hash"]
                    salt = str(config["encryption"]["salt"])
                    print("distance: "+ str(difference))
                    config_data_hash = config["encryption"]["config_data_hash"]
                    config_salt = config["encryption"]["config_salt"]
                    #TODO: check hash 
                    if encrypt.check_hash(encrypt.open_file(filename), salt) == data_hash:
                        print("same hash")
                    else:
                        pass
                        print("not the same hash")
                        print(data_hash)
                        print(encrypt.check_hash(encrypt.open_file(filename), salt))
                    serial_connection.close()
                    gps_event.clear()
                    gps_thread.join()
                    exit("end")
                else:
                    print("wrong OTP last try!")
                    if check_2fa(int(input("OTP: ")), totp):  
                        encrypt.symmetric_decrypt(filename, symmetric_key)
                        print("in radius - file is decrypted")
                        GPIO.output(led_red, GPIO.LOW)
                        GPIO.output(led_yellow, GPIO.LOW)
                        GPIO.output(led_green, GPIO.HIGH)
                        os.remove(encrypted_key_file_path)
                        data_hash = config["encryption"]["data_hash"]
                        salt = str(config["encryption"]["salt"])
                        print("distance: "+ str(difference))
                        #TODO: check hash 
                        if encrypt.check_hash(encrypt.open_file(filename), salt) == data_hash:
                            print("same hash")
                        else:
                            pass
                            print(data_hash)
                            print(encrypt.check_hash(encrypt.open_file(filename), salt))
                        serial_connection.close()
                        gps_event.clear()
                        gps_thread.join()
                        exit("Ende")
                    else:
                        exit("wrong OTP - everything deleted")
            else:
                print("outside of the radius")
            print("distance: "+ str(difference))
            print("speed over ground: "+ str(speed_over_ground))
            time.sleep(0.5)
            GPIO.output(led_red, GPIO.LOW)
            GPIO.output(led_yellow, GPIO.LOW)
            GPIO.output(led_green, GPIO.LOW)
            time.sleep(0.5)
            GPIO.output(led_red, GPIO.LOW)
            GPIO.output(led_yellow, GPIO.HIGH)
            GPIO.output(led_green, GPIO.LOW)
    except KeyboardInterrupt:
        serial_connection.close()
        gps_event.clear()
        gps_thread.join()
        exit("end")

# encrypt.symmetric_decrypt(filename, symmetric_key)


#Abfrage was machen
questions = [
  inquirer.List('choise',
                message="What do you want to do?",
                choices=['encrypt', 'decrypt'],
            ),
]
try:
    answers = inquirer.prompt(questions)
    GPIO.output(led_red, GPIO.LOW)
    GPIO.output(led_yellow, GPIO.LOW)
    GPIO.output(led_green, GPIO.HIGH)
    if answers["choise"] == "encrypt":
        questions = [
        inquirer.List('choise',
                        message="Do you want to use your onw coordinates",
                        choices=['yes', 'no'],
                    ),
        ]
        answers = inquirer.prompt(questions)
        if answers["choise"] == "yes":
            GPIO.output(led_red, GPIO.LOW)
            GPIO.output(led_yellow, GPIO.HIGH)
            GPIO.output(led_green, GPIO.LOW)
            input_gps_coordinates()
            encryption_process()
            GPIO.output(led_red, GPIO.HIGH)
            GPIO.output(led_yellow, GPIO.LOW)
            GPIO.output(led_green, GPIO.LOW)
        elif answers["choise"] == "no":
            GPIO.output(led_red, GPIO.LOW)
            GPIO.output(led_yellow, GPIO.HIGH)
            GPIO.output(led_green, GPIO.LOW)
            encryption_process()
            GPIO.output(led_red, GPIO.HIGH)
            GPIO.output(led_yellow, GPIO.LOW)
            GPIO.output(led_green, GPIO.LOW)
        else:
            raise Exception("Error: question not chosen")
    elif answers["choise"] == "decrypt":
        GPIO.output(led_red, GPIO.LOW)
        GPIO.output(led_yellow, GPIO.HIGH)
        GPIO.output(led_green, GPIO.LOW)
        decryption_process()
    else:
        raise Exception("Error: question not chosen")
except TypeError:
    exit("end")

#GPIO.cleanup()