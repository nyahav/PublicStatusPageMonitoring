# Public Status Page Monitoring
The script traverses a RSS\Atom feed of a public statuspage, 
finds keywords in recent events posted to the statuspage from a list of services
and returns a matching Icinga status code. 


## Pre requisites

Create a JSON file in the following format : 
```
{
    "url": <url> ,
    "name" : <service_mame> ,
    "event_tag": <event_Tag> ,
    "time_tag": <time_tag> ,
    "service_names" : ["NAME 1","NAME 2" , ... ] , 
    "keywords": {
        <keyword> : <severity> ,
        ...

    }
    "date_format" : <date_format>  
}
```

1. **url** - Url of the Atom feed. 
2. **name** -  Name of the service.
3. **event_tag** - The tag in the Atom feed that is given to events (commonly'entry') .
4. **time_tag** - The tag listing the event publication. (such as 'published' or 'updated') .
5. **service names** - A list (in square brackets ) of all the services that should be tracked - often not all the services in a statusapage are used internally , so you need to provide the exact name of the service as it is called (case sensetive) . 
If left empty, all services will be considered. 
6. **keywords** - A dictionary of keywords to determine event severity. For example, the keyword 'downtime' could signify a severe incident.
7. **date format**  -  A statusapage may use a differnt time format or time zone 
    A format template is used to match the components of the datetime string you want to parse. You create it using placeholders that correspond to the components in your datetime string. Here are some common placeholders:

    %Y: Year with century as a decimal number (e.g., 2023)
    %m: Month as a zero-padded decimal number (01 to 12)
    %d: Day of the month as a zero-padded decimal number (01 to 31)
    %H: Hour (24-hour clock) as a zero-padded decimal number (00 to 23)
    %M: Minute as a zero-padded decimal number (00 to 59)
    %S: Second as a zero-padded decimal number (00 to 59)

    If no date format is provided the script would default to ISO 8601 date format ( "%Y-%m-%dT%H:%M:%SZ" ) that is often used in statuspages (commonly statuspages hosted by Atlassian Statuspage) . 

