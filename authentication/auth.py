import bcrypt
from authentication.database import add_user, get_user


def hash_password(password):
    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    )


def signup(name, email, password):

    # Check empty fields
    if not name.strip():
        return False, "Username is required"

    if not email.strip():
        return False, "Email is required"

    if not password.strip():
        return False, "Password is required"


    # Check if email already exists
    existing_user = get_user(email)

    if existing_user:
        return False, "This email is already exists"


    # Password length check
    if len(password) < 8:
        return False, "Password must be at least 8 characters"


    # Encrypt password
    hashed_password = hash_password(password)


    # Add user to database
    add_user(
        name,
        email,
        hashed_password
    )


    return True, "Account created successfully"


def login(email, password):

    if not email.strip():
        return False

    if not password.strip():
        return False

    user = get_user(email)

    if user:

        stored_password = user["password"].encode("utf-8")

        if bcrypt.checkpw(
            password.encode(),
            stored_password
        ):
            return True

    return False