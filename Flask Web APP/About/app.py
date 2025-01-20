from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index1.html')  # Correctly render the HTML file

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1000, debug=True)
