import os
import asyncio

import logging
import clearbit
import time

from tide_test.app import app
from tide_test.validator import validator
from tide_test.company_view.models import Company, Domain_information
from faust.web import Request, Response, View

companies_topic = app.topic('companies', partitions=1, value_type=Company)

domain_info_topic = app.topic('domain_information', partitions=1, value_type=Domain_information)

company_table = app.Table('company_record',partitions=1, default=int)

messages = {} # use as in-memory data-base will be wiped on restart

clearbit.key = os.getenv('CLEARBITACCESSKEY', None)


@app.agent(companies_topic)
async def store_company_views(companies):
    async for company in companies:
        print(f"received message for company {company.name}")
        company.name = company.name.lower()
        messages[company.name] = company
        print(f"Getting more details from clearbit server for {company.name}")
        company_data = clearbit.Company.find(domain=company.domain, stream=True)
        await domain_info_topic.send(value={'clearbitData':company_data,
                                            'name':company.name})


@app.agent(domain_info_topic)
async def store_domaininfo_views(domain_info):
    async for info in domain_info:
        flag = True
        print(f"domain information extraction {info}")
        # print(f"domain information clearbit {info.clearbitData}")
        # print(info.clearbitData['id'],info.clearbitData['name'])
        # print(info.clearbitData['metrics']['employees'],info.clearbitData['foundedYear'])
        company_id = info.clearbitData['id']
        name = info.clearbitData['name'].capitalize()
        metrics_employee = info.clearbitData['metrics']['employees']
        year = info.clearbitData['foundedYear']
        company_domain = info.clearbitData['domain']
        print (company_id,name,metrics_employee,year)
        for c_name in company_table.keys():
            if company_table[c_name]["comp_id"] == company_id:
                flag = False
                #messages.pop(info.name, 'No Key found')
                print('Deleting duplicate record',info.name,company_table[c_name]["comp_id"])
                print(company_table)
                print(type(company_table))
                print(company_table.as_ansitable())
                print('taking a break')
                print(c_name)
                #company_table.pop(c_name, 'No Key found')
                break
        print(messages)
        if flag:
            print(' pushing to table')
            company_table[(name,company_id)] = dict(comp_id=company_id,
            name= name,
            employees=metrics_employee, 
            year= year,
            company_domain=company_domain)
        print(' doing the right thing')



@app.page('/companies/')
class counter(View):
    async def get(self, request):
        print (company_table.as_ansitable())
        print (len(company_table.keys()))
        print (company_table.keys())
        sync_start = len(company_table.keys())
        if sync_start ==0:
            await sync_table_inmemdb()
        return self.json({'messages': messages})

    async def post(self, request):
        body = await request.json()
        print(body)
        msg, body, flag = validator(messages, body)
        print(msg)
        if flag:
            await companies_topic.send(value=body)
            return self.json({'processed': True,'exists': False})
        else:
            return self.json({'processed': False,'exists': True})

@app.page('/companies/{name}')
@app.table_route(table=company_table, match_info='name')
async def hashtag_count(self, request, name):
    result = company_table.get(name.capitalize())
    if result:
        return self.json({'Company': name, 'Data': company_table[name]})
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
                body['name'] = comp
                body['domain'] = company_table[comp]["company_domain"]
                await companies_topic.send(value=body)
            break



logger = logging.getLogger(__name__)



