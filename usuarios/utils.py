import re
import secrets
import unicodedata
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.strip().encode('utf-8')).hexdigest()

def generate_username(apellido: str, nombre: str) -> str:
    def clean(text: str) -> str:
        text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
        text = re.sub(r'[^a-zA-Z0-9]', '', text)
        return text.lower()
    
    clean_ape = clean(apellido.strip().split()[0] if apellido.strip() else 'usuario')
    first_name_parts = nombre.strip().split()
    first_letter = clean(first_name_parts[0])[0] if first_name_parts and clean(first_name_parts[0]) else 'x'
    return f"{clean_ape}{first_letter}"

def validate_strong_password(password: str) -> tuple[bool, str]:
    p = password.strip()
    if len(p) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r'[A-Z]', p):
        return False, "La contraseña debe contener al menos una letra MAYÚSCULA (A-Z)."
    if not re.search(r'[a-z]', p):
        return False, "La contraseña debe contener al menos una letra MINÚSCULA (a-z)."
    if not re.search(r'[0-9]', p):
        return False, "La contraseña debe contener al menos un NÚMERO (0-9)."
    if not re.search(r'[^A-Za-z0-9]', p):
        return False, "La contraseña debe contener al menos un caracter ESPECIAL (!@#$%&*-_)."
    return True, ""

def generate_temp_password(length: int = 10) -> str:
    mayus = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    minus = 'abcdefghjkmnpqrstuvwxyz'
    nums = '23456789'
    specs = '!@#$%*-_'
    chars = [secrets.choice(mayus), secrets.choice(minus), secrets.choice(nums), secrets.choice(specs)]
    all_chars = mayus + minus + nums + specs
    for _ in range(length - 4):
        chars.append(secrets.choice(all_chars))
    secrets.SystemRandom().shuffle(chars)
    return ''.join(chars)
