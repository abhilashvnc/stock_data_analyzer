from nsetools import Nse
def nse_tools_fetch():
    nse = Nse()
    quote = nse.get_quote("reliance")

    print(quote)
    
print(nse_tools_fetch())