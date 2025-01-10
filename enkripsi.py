import os
from cryptography.fernet import Fernet

def main():
    print("Welcome to the File Encryption Tool!")
    
    # Ask for the original file location
    original_file_path = input("Enter the original file location (e.g., play.py): ")
    
    # Check if the file exists
    print(f"Checking file at: {original_file_path}")  # Debugging line
    if not os.path.isfile(original_file_path):
        print("The specified file does not exist or is not a file. Please check the path.")
        return

    # Ask for the location to save the key
    key_file_path = input("Enter where you want to save the encryption key (e.g., config.key): ")
    
    # Check if the provided key file path is valid
    if os.path.isdir(key_file_path):
        print("Please provide a valid file path for the encryption key, including the filename.")
        return

    # Ask for the location to save the encrypted file
    encrypted_file_path = input("Enter where you want to save the encrypted file (e.g., config.py): ")
    
    # Check if the provided encrypted file path is valid
    if os.path.isdir(encrypted_file_path):
        print("Please provide a valid file path for the encrypted file, including the filename.")
        return

    # Generate a key and save it
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)

    # Save the key to the specified file location
    with open(key_file_path, 'wb') as key_file:
        key_file.write(key)
    print(f"Encryption key saved as {key_file_path}.")

    # Read the code from the original file
    with open(original_file_path, 'rb') as file:
        code = file.read()
    print(f"Read {len(code)} bytes from {original_file_path}.")

    # Encrypt the code
    encrypted_code = cipher_suite.encrypt(code)
    print(f"Encrypted the code from {original_file_path}.")

    # Save the encrypted code to the specified file location
    with open(encrypted_file_path, 'wb') as enc_file:
        enc_file.write(encrypted_code)
    print(f"Encrypted code saved as {encrypted_file_path}.")

    print("Encryption process completed successfully.")

if __name__ == '__main__':
    main()
