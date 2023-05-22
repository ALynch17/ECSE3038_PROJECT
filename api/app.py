import os
from fastapi import  FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, JSONResponse
import motor.motor_asyncio
from bson import ObjectId
import pydantic
import requests
import re
from dotenv import load_dotenv 
from datetime import datetime,timedelta

load_dotenv()

app = FastAPI()

origins=[
    "https://al-ecse3038-project.onrender.com",
    "https://simple-smart-hub-client.netlify.app"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client= motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://week4:oKbzC9wuJa6nIJKI@cluster0.ldjatx3.mongodb.net/?retryWrites=true&w=majority")
db= client.smarthub_control

pydantic.json.ENCODERS_BY_TYPE[ObjectId]=str

regex = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')

def parse_time(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)

def getsunset():
    sunresponse= requests.get(f'https://api.sunrise-sunset.org/json?lat=18.1096&lng=-77.2975&date=today')
    sunrep= sunresponse.json()

    sunset= sunrep["results"]["sunset"]
    sunset_time= datetime.strptime(sunset, "%I:%M:%S %p") + timedelta(hours=-5)
    newsunset_time = datetime.strftime(sunset_time,"%H:%M:%S")

    return newsunset_time

@app.post("/api/state",status_code=201)
async def create_state(request:Request):
    createdstate=await request.json()
    createdstate["datetime"]=(datetime.now()+timedelta(hours=-5)).strftime('%Y-%m-%dT%H:%M:%S')

    new= await db["state"].insert_one(createdstate)
    updated = await db["state"].find_one({"_id":new.inserted_id})

    if new.acknowledged == True:
        return updated
    raise HTTPException(status_code=400,detail="Client Error - Unable to Process Request")
    
@app.put("/settings", status_code=201)
async def create_and_update_settings(request:Request):
    sett2 = await request.json()
    data = await db["settings"].find().to_list(1)

    mod={}
    mod["user_temp"]=sett2["user_temp"]
    

    if sett2["user_light"]=="sunset":
        time=getsunset()
    else:
        time=sett2["user_light"]
    mod["user_light"]=(datetime.now().date()).strftime("%Y-%m-%dT")+time
    mod["light_time_off"]=((datetime.strptime(mod["user_light"],'%Y-%m-%dT%H:%M:%S')+parse_time(sett2["light_duration"])).strftime('%Y-%m-%dT%H:%M:%S'))

    if len(data)==0:
         new_sett = await db["settings"].insert_one(mod)
         patched_sett = await db["settings"].find_one({"_id": new_sett.inserted_id })
         return patched_sett
    else:
        id=data[0]["_id"]
        updated_sett= await db["settings"].update_one({"_id":id},{"$set": mod})
        patched_sett = await db["settings"].find_one({"_id": id})
        if updated_sett.modified_count>=1: 
            return patched_sett
    raise HTTPException(status_code=400,detail="Bad request")


    
    

@app.get("/graph")
async def get_graph(request:Request,size:int):
    n=size
    arrayofstates= await db["state"].find().sort("datetime",-1).to_list(n)
    arrayofstates.reverse()

    return arrayofstates
 
@app.get("/api/state")
async def get_state():
    
    currentstate= await db["state"].find().sort("datetime",-1).to_list(1)
    currentsett= await db["settings"].find().to_list(1)

    distsens=currentstate[0]["presence"]

    currenttime= datetime.strptime(datetime.strftime(datetime.now()+ timedelta(hours=-5), '%H:%M:%S'),'%H:%M:%S')
    usertime=datetime.strptime(currentsett[0]["user_light"],'%H:%M:%S')
    time_off=datetime.strptime(currentsett[0]["light_time_off"],'%H:%M:%S')

    fan = ((float(currentstate[0]["temperature"])>float(currentsett[0]["user_temp"])) and distsens)
    light = (currenttime>usertime) and (distsens) and (currenttime<time_off)

    cstate={"fan":fan,"light":light}
    return cstate
