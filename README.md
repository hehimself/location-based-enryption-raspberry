# Location based encryption in Python 

![sheme](/documentation/scheme.png)
[![sheme]/documentation/scheme.png](./example.svg)
## GeoLock Algorithm
The project algorithm is inspired by the  GeoCodex GeoEncryption Algoritm. (References: [A Location Based Encryption Technique and Some of its Applications by Locan Scott](https://faculty.nps.edu/dedennin/publications/ION_GPS_2003_DC_VF.pdf))


## Requirements
```bash
pip install pyotp
pip install cryptography
pip install inquirer
pip install pynmea2
```

## Functionality
### Encryption
1. Hash the data and the config for dataintegrity 
2. generate a random symmetric key (key_s)
3. Encrypt the plaintext (file) with the symmetric key (key_s)
4. generate a random rsa_keys (key_e = public, key_d = private)
5. Encrypt the config file with the symmetric key (key_s)
6. Enrcrypt the symmetric_key (key_s) with the public key (key_e)

The config file with the coordinates and the data file is now encrypted and could be send safely. 

### Decryption
1. Decrypt the symmetric_key (key_s) with the private key (key_d)
2. Decrypt the config file with thee symmetric key (now the all the variables should be loaded into ram and after that the config file should be delted automaticly)
3. Get the current GPS-Position (GPS-Sensor over Serial0)
4. If the GPS-Position is the correct one with a little bit of tolerance defined in the config file with the radius (mapping function)
5. Position correct -> Ask for the One Time Password (2 tries)
6. Encrypt the data (file) with the symmetric key (key_s)
7. check with the hash if the Data got corrupted

## Modules
In these Modules there are several functions to enrcrypt and decrypt the data. Moreover sort of a mapping technique is used, following [A Location Based Encryption Technique and Some of its Applications by Locan Scott](https://faculty.nps.edu/dedennin/publications/ION_GPS_2003_DC_VF.pdf).


```python
from location_encrypt import encrypt
from location_encrypt import mapping
```
However, my algorithm might even be more secure, as it integrates 2FA in addition to the hybrid encryption technique.
