from nsetools import Nse
def nsetools_fetch():
    nse = Nse()
    quote = nse.get_quote("reliance")

    print(quote)
    
print(nsetools_fetch())