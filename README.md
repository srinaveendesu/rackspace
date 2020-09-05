TIDE-code-challenge
====================

This project contains code boiler-plate code for a faust project


You can start the project using the commands


```
make clean
make run-dev
```

it spins up three docker containers, the faust project as well as two kafka-containers. There is one topic on kafka, companies


You can try to post to the endpoint `/http://localhost:6066/companies/` 

the value

```
{
	"name": "Tide",
	"domain": "tide.co"
}
```

in order to add this as a message to the topic.

You can see the current state of the topic by performing a get-request to the url `/http://localhost:6066/companies/` 


Task:
--------
- Sign up to the clearbit API (https://clearbit.com/docs#api-reference)
- Adjust the worker such that whenever there is a new message on the bus, we call the `companies` endpoint of clearbit and put the json response on a new topic `domain_information`
- Adjust the worker such that there is an agent which subscribes to the `domain_information` topic, extracts the number of employess and age of the company (based on founded date) and stores it within a table 
- Expose an endpoint `/companies/{name}` which exposes the number of employees and the age of the company for a particular company name (that was put on the companies topic)

Please ensure the code is production-ready, that is edge cases are handled and the code is tested.