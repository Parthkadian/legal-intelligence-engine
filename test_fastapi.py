import traceback
try:
    print("Importing main")
    from api.main import app
    from fastapi.testclient import TestClient
    
    print("Testing startup")
    with TestClient(app) as client:
        r = client.get("/health")
        print(r.status_code)
except Exception as e:
    with open("fatal_error.txt", "w") as f:
        f.write(traceback.format_exc())
    print("Wrote fatal_error.txt")
