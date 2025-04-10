from src.database import connect_to_db

def main():
    engine = connect_to_db()
    print("Connected to the census database!")

if __name__ == "__main__":
    main()
