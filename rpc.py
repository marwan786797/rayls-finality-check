import json, urllib.request
R="https://mainnet-rpc.rayls.com"
def call(m,p=[]):
    req=urllib.request.Request(R,data=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode(),headers={"content-type":"application/json","user-agent":"Mozilla/5.0"})
    return json.load(urllib.request.urlopen(req,timeout=30))
def batch(reqs):
    body=[{"jsonrpc":"2.0","id":i,"method":m,"params":p} for i,(m,p) in enumerate(reqs)]
    req=urllib.request.Request(R,data=json.dumps(body).encode(),headers={"content-type":"application/json","user-agent":"Mozilla/5.0"})
    r=json.load(urllib.request.urlopen(req,timeout=60))
    return [x.get("result") for x in sorted(r,key=lambda x:x["id"])]
