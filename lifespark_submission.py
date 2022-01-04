#### package imports
import csv
import numpy as np
import datetime
from dateutil.parser import parse


#### turn CSVs into dictionaries


#### member dictionary

# open CSV and turn it into an array
membercsv =  open('lifespark_members.csv','r')
members_array = list(csv.reader(membercsv))

# get the keys and turn into a dictionary using the member_id as the primary key
member_data_keys = members_array[0]
member_dictionary={}
for members in members_array[1:]:
    member_id = members[0]
    member_data = dict(zip(member_data_keys[1:], members[1:]))
    member_dictionary[member_id] = member_data

#### hospital codes dictionary

codes_csv =  open('hospital_codes.csv','r')
codes_array = list(csv.reader(codes_csv))

codes_keys = codes_array[0][1:]
codes_dictionary={}
for code in codes_array[1:]:
    code_data={}
    code_info = dict(zip(codes_keys, code[1:]))
    codes_dictionary[code[0]] = code_info



#### hospital procedures dictionary

# open CSV and turn it into an array
procedure_csv =  open('hospital_procedures.csv','r')
procedure_array = list(csv.reader(procedure_csv))

# in the case of procedures, I'm going to use nested dictionaries, because we may need to use procedure ID but likely we'll want to aggregate by member_id

# get the keys and turn into a dictionary
procedure_keys = procedure_array[0][1:]
procedure_dictionary={}

for procedure in procedure_array[1:]:
    member_procedure={}

    # get cost of procedure based off of code
    if procedure[6] != '':
        cost = 0
        for code, info in codes_dictionary.items():
            if info['code'] == procedure[6]: 
                #adding in a max function in case there are duplicates. I figure it's best to go with the most expensive cost
                if cost == 0:
                    cost = info['cost']
                else:
                    cost = max(cost, info['cost'])
        procedure_keys.append('cost')
        procedure.append(cost)        
    #calculate length of stay based off admission

    #convert admission date to date
    if procedure[7] != '':
        admission_date = parse(procedure[7])
        procedure[7] = admission_date.strftime('%m/%d/%Y')

    #convert disccharge date to date
    if procedure[8] != '':
        discharge_date = parse(procedure[8])
        procedure[8] = discharge_date.strftime('%m/%d/%Y')

    #length_of_stay
    if procedure[7] != '' and procedure[8] != '':
        length_of_stay = parse(procedure[8]) - parse(procedure[7])
        procedure_keys.append('length_of_stay_in_days')
        procedure.append(length_of_stay.days)

    member_procedure = dict(zip(procedure_keys, procedure[1:]))
    #add to dictionary
    procedure_dictionary[procedure[0]] = member_procedure

################
################################
################ Question 1: 10 members, highest cost
################################
################

### Create a dictionary to aggregate costs at member id level

total_costs = {}
for procedure, info in procedure_dictionary.items():
    if info['member_id'] in total_costs.keys():
        total_costs[info['member_id']] += int(info['cost'])
    else:
        total_costs[info['member_id']] = int(info['cost'])

### get top x members with high costs

from operator import itemgetter

print('How many of the top cost would you like to see?')
number_of_terms = input()
while number_of_terms.isnumeric() == False:
    if number_of_terms.isdigit() == False:
        print ("I'm sorry, whole numbers only. How many members would you like to see?")
        number_of_terms = input()

def top_x(total_costs, number_of_terms):
    top_x = sorted(total_costs.items(), key = itemgetter(1), reverse = True)[0:number_of_terms]
    return top_x

################
################################
################ Question 2: Cost by admission day of week
################################
################

weekday_costs = {}
for procedure, info in procedure_dictionary.items():
    if info['admission_date'] == '':
        pass
    else: 
        weekday = parse(info['admission_date']).weekday()
        if weekday in weekday_costs.keys():
            weekday_costs[weekday] += int(info['cost'])
        else:
            weekday_costs[weekday] = int(info['cost'])

weekday_admissions = {}
for procedure, info in procedure_dictionary.items():
    if info['admission_date'] == '':
        pass
    else: 
        weekday = parse(info['admission_date']).weekday()
        if weekday in weekday_admissions.keys():
            weekday_admissions[weekday] += 1
        else:
            weekday_admissions[weekday] = 1

### however this is out of order for the request as day 0 is monday in python
### at the same time, the CFO may change their mind later and want it to start with monday. Therefore we should double check:
print('Which weekday would you like to start with?')
weekday = input()

import time
import calendar

weekday_as_int = 7
while weekday_as_int > 6:
    try:
        if len(weekday) > 3:
            weekday_as_int = time.strptime(weekday, "%A").tm_wday
        else:
            weekday_as_int = time.strptime(weekday, "%a").tm_wday
    except:
        print ("I'm sorry, that's not a day of the week I recognize. I recognize days like 'monday' or 'tuesday':")
        weekday = input()

def ordered_weekday_costs_and_admissions(weekday_admissions, weekday_costs, weekday_as_int):
    ordered_results={}   
    for i in range(0,7):
        # if they wanted to start at day 6, for example, the next day will be day 7... which is day 0
        if weekday_as_int > 6:
            weekday_as_int -= 7
        weekday_name = calendar.day_name[weekday_as_int]
        ordered_results[weekday_name] = {'costs': weekday_costs[weekday_as_int], 'admissions': weekday_admissions[weekday_as_int]}
        weekday_as_int += 1
    return(ordered_results)



################
################################
################ Question 3: Readmittance in last thirty days
################################
################


### For this, I'll put in another input as they may want last 30, 60, 90, etc days

# get current date in the same format as the dictionaries 
from datetime import datetime
now = datetime.now()
now_str = now.strftime('%m/%d/%Y')


#get lookback window
print('How many days back would you like to look?')
number_of_days = input()
while number_of_days.isnumeric() == False:
    if number_of_days.isdigit() == False:
        print ("I'm sorry, whole numbers only. How many days back would you like to look?")
        number_of_days = input()



## get an array of admissions within this window
admissions = []
for procedure, info in procedure_dictionary.items():
    if info['admission_date'] == '':
        pass
    else:
        date_delta = parse(now_str) - parse(info['admission_date'])
        if date_delta.days >= number_of_days:
            pass
        else: 
            ### I am not de-duping here because a patient could have come in multiple times within this window. Each of those would count as a readmittance
            admissions.append([info['member_id'], info['admission_date']])

## find out how many of these are readmissions
## I'm defining this as patients who have been treated previously

readmissions = []
for patient in admissions:
    patient_id = patient[0]
    patient_admission_date = patient[1]
    for procedure, info in procedure_dictionary.items():
        if info['member_id'] == patient_id:
            if info['admission_date'] == '':
                pass
            else:
                date_delta = parse(patient_admission_date) - parse(info['admission_date'])
                if date_delta.days > 0:
                    pass
                else: 
                    if patient_id in readmissions:
                        pass
                    else:
                        readmissions.append(patient_id)

print(readmissions)


################
################################
################ Question 4: Longest Admissions
################################
################