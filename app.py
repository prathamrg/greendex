import json
import requests
from flask import Flask, redirect, session
from flask import render_template, request
from stellar_sdk import Keypair, Network, Server, TransactionBuilder



"""
prefund an account    : https://friendbot.stellar.org/?addr=GB367AJZAEPBTBYSN4D42PZCBSL4GZCSBI2TCNCOZFZDGH44JM5NOL7T
check account balance : https://horizon-testnet.stellar.org/accounts/GB367AJZAEPBTBYSN4D42PZCBSL4GZCSBI2TCNCOZFZDGH44JM5NOL7T
check transactions    : https://horizon-testnet.stellar.org/accounts/GB367AJZAEPBTBYSN4D42PZCBSL4GZCSBI2TCNCOZFZDGH44JM5NOL7T/transactions
laboratory            : https://laboratory.stellar.org/#?network=test
"""
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

with open('assets.json', 'r') as f: assets = json.load(f)
horizon_server = 'https://horizon-testnet.stellar.org'

def create_buy_sell_offer(offer_type, sa, ba, amt, price):
    for asset in assets:
        if asset["ASSET"]==sa:
            si = asset["ISSUER"]
        if asset["ASSET"]==ba:
            bi = asset["ISSUER"]

    server = Server(horizon_server)
    source_keypair = Keypair.from_secret(session["user"]["sk"])
    source_public_key = source_keypair.public_key
    source_account = server.load_account(source_public_key)
    if offer_type == "buy":
        transaction = (TransactionBuilder(source_account=source_account) \
                        .append_manage_buy_offer_op(selling_code=sa if sa!="Native" else "XLM", 
                                                    selling_issuer=si if si!="" else None, 
                                                    buying_code=ba if ba!="Native" else "XLM", 
                                                    buying_issuer=bi if bi!="" else None, 
                                                    amount=str(amt), 
                                                    price=str(price), 
                                                    offer_id=0, 
                                                    source=None) \
                        .build()
                   )
    if offer_type == "sell":
        transaction = (TransactionBuilder(source_account=source_account) \
                        .append_manage_sell_offer_op(selling_code=sa if sa!="Native" else "XLM", 
                                                    selling_issuer=si if si!="" else None, 
                                                    buying_code=ba if ba!="Native" else "XLM", 
                                                    buying_issuer=bi if bi!="" else None, 
                                                    amount=str(amt), 
                                                    price=str(price), 
                                                    offer_id=0, 
                                                    source=None) \
                        .build()
                   )
    transaction.sign(source_keypair)
    response = server.submit_transaction(transaction)
    return response

@app.route("/", methods=['GET'])
def home():
    return render_template('home.html')
    
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pk = request.form.get("pk")
        sk = request.form.get("sk")
        session["user"] = {"pk":pk, "sk":sk}
        return render_template("login_success.html", pk=pk)
    return render_template('login.html')

    

@app.route("/offers", methods=['GET'])
def list_offers():
    items=[]
    for asset in assets:
        if asset["ASSET"]=="Native":
            continue
            #response = requests.get('https://horizon-testnet.stellar.org/offers?selling=native')
            #issuer = 'STLR'
            
        else:
            response = requests.get('{}/offers?selling={}%3A{}'.format(horizon_server,asset['ASSET'],asset['ISSUER']))
            issuer = asset['ISSUER'][:4]
        
        offers = json.loads(response.text)["_embedded"].get("records")
        for offer in offers:
            ba_icon = ""
            for ba in assets:
                if ba["ASSET"] == offer["buying"].get("asset_code", "Native"): ba_icon=ba["URL"]
                
            items.append({"ASSET_ICON":asset["URL"],
                          "ASSET":asset["ASSET"],
                          "ISSUER":issuer,
                          "SELLER":offer["seller"][:4],
                          "BUY_ASSET_ICON":ba_icon,
                          "BUY_ASSET": offer["buying"].get("asset_code", "Native"),
                          "QTY":offer["amount"],
                          "PRICE":offer["price"],
                          "TIME":offer["last_modified_time"]
                          })
    
    
    return render_template('offers.html', items=items)

@app.route("/buy", methods=['GET', 'POST'])
def buy():
    if request.method == 'GET':
        return render_template("create_buy_offer.html")
        
    if request.method == 'POST':
        sa,ba = request.form.get("sa"), request.form.get("ba")
        si,bi = None, None
        amt, price = request.form.get("amt"), request.form.get("price")
        response = create_buy_sell_offer("buy", sa, ba, amt, price)
        return response
    
@app.route("/sell", methods=['GET', 'POST'])
def sell():
    if request.method == 'GET':
        return render_template("create_sell_offer.html")
        
    if request.method == 'POST':
        sa,ba = request.form.get("sa"), request.form.get("ba")
        si,bi = None, None
        amt, price = request.form.get("amt"), request.form.get("price")
        response = create_buy_sell_offer("sell", sa, ba, amt, price)
        return response
        
@app.route("/portfolio", methods=['GET'])
def portfolio():
    
    source_keypair = Keypair.from_secret(session["user"]["sk"])
    pk             = session["user"]["pk"]
    
    response = requests.get("https://horizon-testnet.stellar.org/accounts/{}".format(source_keypair.public_key))
    balances = json.loads(response.text).get("balances")
    
    items = []
    for balance in balances:
        bal           = balance["balance"]
        a             = balance.get("asset_code", "Native")
        ai            = balance.get("asset_issuer", "STLR")[:4]
        bl            = balance["buying_liabilities"]
        sl            = balance["selling_liabilities"]
        url=""
        for asset in assets:
            if asset["ASSET"]==a:
                url=asset["URL"]
        items.append(
                    {"bal":bal, "a":a, "ai":ai, "bl":bl, "sl":sl, "url":url}
                   )
    
    
    
    return render_template('portfolio.html', pk=pk, items=items)

if __name__ == "__main__":
    

    app.run(debug=True)
