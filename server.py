import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import hashlib
import base64
import time
import urllib.parse

DATA_FILE = "users.json"
UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


def load_users():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


class Handler(SimpleHTTPRequestHandler):

    def send_json(self, data):
        response = json.dumps(data).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()

        self.wfile.write(response)


    def do_GET(self):

        if self.path.startswith("/api/user?username="):

            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)

            username = params.get("username", [""])[0]

            users = load_users()

            if username not in users:

                self.send_json({
                    "success": False,
                    "message": "User not found"
                })

                return

            user = users[username]

            self.send_json({
                "success": True,
                "username": username,
                "email": user["email"],
                "points": user["points"],
                "invite_code": user["invite_code"]
            })

            return


        if self.path == "/api/screenshots":

            files = []

            for filename in os.listdir(UPLOAD_DIR):

                path = os.path.join(
                    UPLOAD_DIR,
                    filename
                )

                if os.path.isfile(path):

                    files.append({
                        "filename": filename,
                        "url": "/uploads/" + filename
                    })

            self.send_json({
                "success": True,
                "files": files
            })

            return


        super().do_GET()


    def do_POST(self):

        length = int(
            self.headers.get(
                "Content-Length",
                0
            )
        )

        body = self.rfile.read(length)


        try:

            data = json.loads(body)

        except:

            self.send_json({
                "success": False,
                "message": "Invalid data"
            })

            return


        # SIGNUP
        if self.path == "/api/signup":

            username = data.get(
                "username",
                ""
            ).strip()

            email = data.get(
                "email",
                ""
            ).strip()

            password = data.get(
                "password",
                ""
            ).strip()

            invite_code = data.get(
                "inviteCode",
                ""
            ).strip().upper()


            if not username or not email or not password:

                self.send_json({
                    "success": False,
                    "message": "Please fill all fields."
                })

                return


            users = load_users()


            if username in users:

                self.send_json({
                    "success": False,
                    "message": "Username already exists."
                })

                return


            users[username] = {

                "email": email,

                "password":
                    hash_password(password),

                "points": 20,

                "invite_code":
                    username.upper()

            }


            inviter_found = False


            if invite_code:

                for user in users.values():

                    if user["invite_code"].upper() == invite_code:

                        user["points"] += 50

                        inviter_found = True

                        break


            save_users(users)


            self.send_json({

                "success": True,

                "message":
                    "Account created successfully.",

                "username": username,

                "email": email,

                "points": 20,

                "inviterFound":
                    inviter_found

            })

            return


        # LOGIN
        if self.path == "/api/login":

            username = data.get(
                "username",
                ""
            ).strip()

            password = data.get(
                "password",
                ""
            )


            users = load_users()


            if username not in users:

                self.send_json({
                    "success": False,
                    "message": "Account not found."
                })

                return


            user = users[username]


            if user["password"] != hash_password(password):

                self.send_json({
                    "success": False,
                    "message": "Wrong password."
                })

                return


            self.send_json({

                "success": True,

                "username": username,

                "email": user["email"],

                "points": user["points"]

            })

            return


        # VIDEO REWARD
        if self.path == "/api/video-reward":

            username = data.get(
                "username",
                ""
            ).strip()


            users = load_users()


            if username not in users:

                self.send_json({
                    "success": False,
                    "message": "User not found."
                })

                return


            users[username]["points"] += 20

            save_users(users)


            self.send_json({

                "success": True,

                "points":
                    users[username]["points"]

            })

            return


        # SCREENSHOT UPLOAD
        if self.path == "/api/upload-screenshot":

            username = data.get(
                "username",
                ""
            ).strip()

            image_data = data.get(
                "image",
                ""
            )


            if not username or not image_data:

                self.send_json({

                    "success": False,

                    "message":
                        "Screenshot missing."

                })

                return


            if not image_data.startswith(
                "data:image/"
            ):

                self.send_json({

                    "success": False,

                    "message":
                        "Invalid image."

                })

                return


            try:

                header, encoded = image_data.split(",", 1)


                extension = "jpg"


                if "png" in header:
                    extension = "png"

                elif "jpeg" in header:
                    extension = "jpg"

                elif "webp" in header:
                    extension = "webp"


                image_bytes = base64.b64decode(encoded)


                safe_username = "".join(

                    c for c in username

                    if c.isalnum()
                    or c in "-_"

                )


                filename = (
                    safe_username
                    + "_"
                    + str(int(time.time()))
                    + "."
                    + extension
                )


                filepath = os.path.join(
                    UPLOAD_DIR,
                    filename
                )


                with open(
                    filepath,
                    "wb"
                ) as f:

                    f.write(image_bytes)


                self.send_json({

                    "success": True,

                    "message":
                        "Screenshot received.",

                    "filename":
                        filename

                })

            except Exception as e:

                self.send_json({

                    "success": False,

                    "message":
                        "Upload failed."

                })

            return


        self.send_json({

            "success": False,

            "message":
                "Unknown request."

        })


print(
    "Team Bunny server running on "
    "http://127.0.0.1:8080"
)


server = ThreadingHTTPServer(
    ("0.0.0.0", int(os.environ.get("PORT", 8080))),
    Handler
)

server.serve_forever()
