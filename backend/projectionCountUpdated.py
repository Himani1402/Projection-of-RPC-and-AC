from flask import Flask, request
import json
import datetime
from datetime import datetime
import math
from backend.RecentValidTimestamp import getValidTimestamps 

app = Flask(__name__)

#load the json file and read the sampleJson.json.
# with open('../json_files/sample_json_1.json', 'r') as jsonData:
#     data = json.load(jsonData)

#function converting all the time units to minutes.  
def convertTimeMinutes(expireTime):
    print('convert')
    value = int(expireTime['value'])
    if expireTime["unit"] == "hours":
        print(int(expireTime['value']) )
        return int(expireTime['value']) * 60 
    elif expireTime["unit"] == "DAILY" or expireTime['unit'] == "days":
        return int(expireTime['value']) * 24 * 60
    elif expireTime["unit"] == "WEEKLY" or expireTime['unit'] == "weeks":
        return int(expireTime['value']) * 24 * 7 * 60
    elif expireTime["unit"] == "MONTHLY" or expireTime['unit'] == "months":
        return int(expireTime['value']) * 24 * 30 * 60
    elif expireTime["unit"] == "YEARLY" or expireTime['unit'] == "years":
        return int(expireTime['value']) * 24 * 365 * 60
    else:
        return 0
    
def convertTimeSeconds(expireTime):
    if expireTime["unit"] == "HOURLY":
        return expireTime['value'] * 60 * 60
    elif expireTime["unit"] == "DAILY" or expireTime['unit'] == "DAYS":
        return expireTime['value'] * 24 * 60 * 60
    elif expireTime["unit"] == "WEEKLY" or expireTime['unit'] == "WEEKS":
        return expireTime['value'] * 24 * 7 * 60 * 60
    elif expireTime["unit"] == "MONTHLY" or expireTime['unit'] == "MONTHS":
        return expireTime['value'] * 24 * 30 * 60 * 60
    elif expireTime["unit"] == "YEARLY" or expireTime['unit'] == "YEARS":
        return expireTime['value'] * 24 * 365 * 60 * 60
    else:
        return 0
    
#converting the string time to datetime object.
# def convertStrToInt(time):
#     hourMin = datetime.strptime(time, "%H:%M")
#     hours = int((hourMin.hour)) * 60
#     minutes = int(hourMin.minute)
#     return hours + minutes

#function converting time string to minutes format.
def convertStrToInt(time):
    hours, minutes = map(int, time.split(':'))
    total_minutes = hours * 60 + minutes
    return total_minutes

#function to give time difference
def time_difference(input_date):
    input_date = datetime.strptime(input_date, "%d:%m:%y %H:%M")
    current_time = datetime.now() #change the now to time stamp.
    # print(type(current_time), type(input_date))
    time_diff =  input_date - current_time
    time_diff_minutes = int(time_diff.total_seconds() / 60)
    return time_diff_minutes

def time_diff_sec(input_date):
    input_date = datetime.strptime(input_date, "%d:%m:%y %H:%M")
    current_time = datetime.now() #change the now to time stamp.
    # print(type(current_time), type(input_date))
    time_diff =  input_date - current_time
    time_diff_minutes = int(time_diff.total_seconds())
    return time_diff_minutes


#funtion to convert recurrence time units into minutes 
def recToUnitMinutes(schedule):
    expire = {
        "unit": schedule["recurrence"],
        "value": schedule["repeatInterval"]["every"]
    }
    return convertTimeMinutes(expire)

def recToUnitSeconds(schedule):
    expire = {
        "unit": schedule['recurrence'],
        "value": schedule['repeatInterval']['every']
    }
    return convertTimeSeconds(expire)
    

#function to calculate the number of projection count for the various protections and their schedules.
# def projectionCount(data, givenTime="04:04:24 11:00"):
# @app.route("/api/givenTime", methods=['POST'])
def projectionCount(data, givenTime):
    givenTimeMin = time_difference(givenTime)
    scheduleCount = {'projectionRun': {}, 'Active':{}}
    
    protection_keys = ['arraySchedules', 'onPremisesSchedules', 'cloudStoreSchedules']
    
    for protection_key in protection_keys:
        protection = data.get(protection_key, [])
        if protection_key == 'arraySchedules':
            protectType = 'SNAPSHOT'
            scheduleCount['projectionRun']['SNAPSHOT'] = {}
        elif protection_key == 'onPremisesSchedules':
            protectType = 'BACKUP'
            scheduleCount['projectionRun']['BACKUP'] = {}
        else:
            protectType = 'CLOUD_BACKUP'
            scheduleCount['projectionRun']['CLOUD_BACKUP'] = {}
        
        for schedule in protection:
            count = 0
            if givenTimeMin > 0: 
                if 'timeRangeStart' in schedule:
                    from_time = schedule['timeRangeStart']
                    until_time = schedule['timeRangeEnd']
                    # print(schedule, 'inside schedule')
                    delta = convertStrToInt(until_time) - convertStrToInt(from_time)
                    print((schedule['backupFrequency']))
                    max_count_per_day = math.ceil(delta / convertTimeMinutes(schedule['backupFrequency']))
                    if givenTimeMin < convertStrToInt(from_time):
                        count = 0
                    elif givenTimeMin > delta:
                        if givenTimeMin < 1440:
                            max = math.ceil(delta / convertTimeMinutes(schedule["backupFrequency"]))
                            count = max
                        else:
                            days_multiple = math.floor(givenTimeMin / 1440)
                            count_1 = days_multiple * math.ceil(delta / convertTimeMinutes(schedule["backupFrequency"]))

                            remain_time = givenTimeMin % 1440
                            if remain_time < convertStrToInt(from_time):
                                count = count_1
                            else:
                                count_2 = math.ceil((remain_time - convertStrToInt(from_time)) / convertTimeMinutes(schedule["backupFrequency"]))
                                count = count_1 + count_2
                    else:
                        if convertTimeMinutes(schedule['retainFor']) > 1440:
                            days_multiple = math.floor(schedule['retainFor'] / 1440)
                            count_1 = days_multiple * max_count_per_day

                            remain_time = givenTimeMin % 1440
                            if remain_time < convertStrToInt(from_time):
                                count = count_1
                            else:
                                count_2 = math.ceil((remain_time - convertStrToInt(from_time)) / convertTimeMinutes(schedule["backupFrequency"]))
                                count = count_1 + count_2
                        else:
                            if convertTimeMinutes(schedule['retainFor']) > delta:
                                count = max
                            else:
                                count = math.ceil(convertTimeMinutes(schedule['retainFor']) / convertTimeMinutes(schedule["backupFrequency"]))
                else:
                    if givenTimeMin and (givenTimeMin) < convertTimeMinutes(schedule['retainFor']):
                        print('hi',schedule)
                        count = math.ceil(((givenTimeMin) - convertStrToInt(schedule['StartAfter'])) / convertTimeMinutes(schedule["backupFrequency"]))
                    else:
                        count = math.ceil((convertTimeMinutes(schedule['retainFor']) - convertStrToInt(schedule['StartAfter']) / convertTimeMinutes(schedule["backupFrequency"])))

                scheduleCount['projectionRun'][protectType][schedule['scheduleName']] = count
            else:
                scheduleCount['projectionRun'][protectType][schedule['scheduleName']] = 0

    print(json.dumps(scheduleCount, indent=4))
    return scheduleCount
        # scheduleCount = {'Active':{}}
        # givenTimeMin = time_difference(givenTime)
        # for protection in data['protections']:
        #     protectType = protection['type']
        #     scheduleCount['Active'][protectType] = {}
        #     for schedule in protection["schedules"]:
        #         count = 0
        #         if givenTimeMin > 0:
        #             expireTimeMinutes = convertTimeMinutes(schedule['expireAfter'])
        #             totalExpireMinutes = expireTimeMinutes
        #             # print(expireTimeMinutes)
        #             n = 1
        #             while True:
        #                 totalExpireMinutes = expireTimeMinutes * n
        #                 # print(schedule['name'], totalExpireMinutes)
        #                 # print('givenTime', givenTimeMin)
        #                 if totalExpireMinutes > givenTimeMin:
        #                     if n>1:
        #                         n -= 1
        #                         totalExpireMinutes = expireTimeMinutes * n
        #                         break
        #                     else:
        #                         totalExpireMinutes = 0
        #                         break
        #                 n += 1
        #             # print('frequency minutes', recToUnitMinutes(schedule['schedule']))
        #             count = math.ceil((givenTimeMin - totalExpireMinutes)/recToUnitMinutes(schedule['schedule']))
        #             scheduleCount['Active'][protectType][schedule['name']] = count
        #         else:
        #             scheduleCount['Active'][protectType][schedule['name']] = 0          
    # print(json.dumps(scheduleCount, indent=4))
    # # getValidTimestamps(data=data, given_time=givenTime, scheduleCount=scheduleCount)
    # return scheduleCount

if __name__ == "__main__":
    app.run(debug=True)