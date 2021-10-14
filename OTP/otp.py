import pyotp
import qrcode
import configparser

config_path = "/home/pi/location-based-encryption-1/config.ini"
img_path = "/home/shares/pi/one_time_password.png"

def save_config(config):
    with open(config_path, "w") as configfile:
        config.write(configfile)

def generate_token(img_path):
    token = pyotp.random_base32()
    link = pyotp.totp.TOTP(token).provisioning_uri(name="test@gmail.de", issuer_name='Secure App')
    img = qrcode.make(link)
    img.save(img_path)
    return token
        
def save_token_in_config(config_path, token):
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    print("token: " + token)
    config["sys"]["otp"] = token
    save_config(config)

if __name__ == "__main__":
    token = generate_token(img_path)
    save_token_in_config(config_path, token)