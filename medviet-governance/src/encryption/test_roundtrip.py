# Chạy trong Python shell
from src.encryption.vault import SimpleVault
vault = SimpleVault()

# Test round-trip
original = "Nguyen Van A - CCCD: 012345678901"
encrypted = vault.encrypt_data(original)
print("Encrypted:", encrypted)

decrypted = vault.decrypt_data(encrypted)
print("Decrypted:", decrypted)
assert decrypted == original, "Encryption round-trip FAILED!"
print("✓ Encryption test passed")
