from flask import Flask, redirect

app = Flask(__name__)

@app.route('/check-pdf')
def check_pdf():
    # Redirect to your deployed Streamlit app
    return redirect("https://pdf-detection-cs6sq8qwjxe3b5sklaw87k.streamlit.app/", code=302)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
