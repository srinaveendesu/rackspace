import os
import asyncio
import requests
import time

import logging
import clearbit

from datetime import date
from tide_test.app import app
from tide_test.util import validator, find_company
from tide_test.company_view.models import Company, Domain_information
from faust.web import Request, Response, View

companies_topic = app.topic('companies', partitions=1, value_type=Company)

domain_info_topic = app.topic('domain_information', partitions=1, value_type=Domain_information)

company_table = app.Table('company_record',partitions=1, default=int)

messages = {} # use as in-memory data-base will be wiped on restart

clearbit.key = os.getenv('CLEARBITACCESSKEY', None)

current_date = date.today()

@app.agent(companies_topic)
async def store_company_views(companies):
    async for company in companies:
        print(f"received message for company {company.name}")
        company.name = company.name.lower()
        try:
            print(f"Getting more details from clearbit server for {company.name}")
            company_data = clearbit.Company.find(domain=company.domain, stream=True)
            if company.name.lower() == company_data['name'].lower():
                messages[(company.name.capitalize(), company_data['id'])] = company
            # Issue: In case when kafka is down/unable to receive messages,
            #         asynchronous publishing will fail.
            # TODO: Can be extended to Synchronized/Asynchronized
            await domain_info_topic.send(value={'clearbitData':company_data,
                                                'name':company.name})
        except requests.exceptions.HTTPError:
            print (f"Invalid domain name given {company.domain}")

@app.agent(domain_info_topic)
async def store_domaininfo_views(domain_info):
    async for info in domain_info:
        flag = True
        company_id = info.clearbitData['id']
        name = info.clearbitData['name'].capitalize()
        metrics_employee = info.clearbitData['metrics']['employees']
        year = info.clearbitData['foundedYear']
        company_domain = info.clearbitData['domain']
        #print (company_id,name,metrics_employee,year)
        for c_name in company_table.keys():
            if company_table[c_name]["comp_id"] == company_id:
                flag = False
                print(f'Company already exists {c_name}')
                break
        print(messages)
        if flag:
            print('Pushing to table')
            company_table[(name,company_id)] = dict(comp_id=company_id,
            name= name,
            employees=metrics_employee, 
            year= year,
            company_domain=company_domain)
        # print(' doing the right thing')



@app.page('/companies/')
class counter(View):
    async def get(self, request):
        print (company_table.as_ansitable())
        print (len(company_table.keys()))
        
        print (company_table.keys())
        global messages
        print(messages)
        sync_start = len(messages)
        print(f'len of in mem db {sync_start}' )
        if sync_start != len(company_table.keys()):
            messages = {}
            await sync_table_inmemdb()
        return self.json({'messages': list(messages.items())})

    async def post(self, request):
        body = await request.json()
        print(body)
        msg, body, flag = validator(messages, body)
        print(msg)
        if flag:
            await companies_topic.send(value=body)
            return self.json({'processed': True,'exists': False})
        else:
            return self.json({'processed': False,'Error': msg})
    

@app.page('/companies/{name}')
@app.table_route(table=company_table, match_info='name')
async def hashtag_count(self, request, name):
    #result = company_table.get(name.capitalize())
    result = {}
    lst = []
    for comp in company_table.keys():
        if comp[0].lower() == name.lower():
            lst.append(comp)
    for element in lst:
        print('output data')
        print(company_table[element]['employees'])
        print(company_table[element]['year'])
        result[element] = dict(No_of_employees=company_table[element]['employees'],
                                                Age=(current_date.year - company_table[element]['year']))
    if result:
        return self.json(list(result.items()))
    else:
        return self.json({'Error': 'No record found'})

async def sync_table_inmemdb():
    rows = len(company_table.keys())
    count = 0
    body = {}
    while count <10:
        count +=1
        print(count)
        print (company_table.as_ansitable())
        print (len(company_table.keys()))
        time.sleep(1)
        if rows>0:
            for comp in company_table.keys():
                body['name'] = company_table[comp]["name"]
                body['domain'] = company_table[comp]["company_domain"]
                await companies_topic.send(value=body)
            break
    return


logger = logging.getLogger(__name__)



