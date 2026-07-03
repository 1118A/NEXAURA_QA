from app import create_app

app = create_app()

if __name__ == "__main__":
    # Start the Flask web application in debug mode locally
    print("Launching NexAura QA Bot on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)