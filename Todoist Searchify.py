# Python3
# -*- coding: utf-8 -*-
import todoist, os
from urllib import quote

"""
Instructions:
1. Create a Todoist label "searchify" or change the user var "customLabelName" below to a name you prefer.
	!! This label will be REMOVED from all tasks during this script! Do not use a label you use for any other purpose.
	!! Unless you change searchCompletedTasks in user vars below, All COMPLETED tasks with this label will be un-completed!
		This is for IFTTT compatibility: The "completed" trigger is the only way to indicate a task at any point after its creation.
		You can complete tasks again once this script has removed the tag, and they will stay completed.
2. Optional: Change the user var "customSearchEngine" below to any url of your choice as long as the name of your task can be appended as the search parameter:
	customSearchEngine = "https://duckduckgo.com/?q="
3. Get your Todoist API Key from here:
	https://todoist.com/prefs/integrations
	Add it to the User var "apiToken" below -OR- save it in the same folder as this script as:
	todoistApiToken.txt
4. Run script.
"""
#### USER VARS ####:

customLabelName = 'searchify' #Match tasks with this task label.
customSearchEngine = "https://www.google.com/search?q=" #Link is made from this string followed by the task name, url-encoded.
apiToken = "" #Paste your API token here to skip reading it from a file.
searchCompletedTasks = 2 #If 0, completed tasks with the tag will be ignored. If 1, completed tasks will be linkified but REMAIN completed. If 2, they will be un-completed after linkification. 


#### FUNCTIONS ####

def find_label_by_name(name):
	for eachLabel in api['labels']:
		if eachLabel['name'].lower() == name.lower():
			return(eachLabel)
	raise Exception("no label found matching: " + name)

def item_is_still_alive(item):
	if item['is_deleted'] == 0 and item['in_history'] == 0:
		return(True)
	else:
		return(False)

def get_items_with_label(labelId, itemList):
	list = []
	for item in itemList:
		if labelId in item['labels']:
			if (searchCompletedTasks > 0 or item_is_still_alive(item)):
				list.append(item)
	return(list)

def url_encode(aString):
    returnString = ""
    for eachCharacter in aString:
    	try:
    		returnString += quote(eachCharacter)
    	except: #quote() fails on unicode characters such as emojis, but they are accepted in urls anyway and don't break Todoist's linkification.
    		returnString += eachCharacter
    return returnString


#### BEGIN ####

#Load API Token:
if apiToken == "":
	try:
		tokenFile = open("todoistApiToken.txt", "r")
	except:
		raise Exception("\nRequires your Todoist API token in this folder: \n" + os.getcwd() + "todoistApiToken.txt \nGet it from: \nhttps://todoist.com/prefs/integrations")
	apiToken = tokenFile.read()

#Sync:
api = todoist.api.TodoistAPI(token=apiToken, api_endpoint='https://todoist.com', session=None, cache='~/.todoist-sync/')
syncResult = api.sync()
if 'error' in syncResult: 
	raise Exception(syncResult['error'] + "\nToken: " + apiToken)

#Get this feature's label:
updatedCount = 0
aLabel = find_label_by_name(customLabelName)

matchedItems = get_items_with_label(aLabel['id'], api.state['items'])
for eachItem in matchedItems:
	taskName = eachItem['content']
	#Check for existing URL format:
	if not ((taskName.startswith("[")) & (taskName.endswith(")")) & ("](" in taskName)):
		#Edit Name:
		urlFormattedTaskName = url_encode(taskName)
		taskName = ("[" + taskName + "](" + customSearchEngine + urlFormattedTaskName + ")")
	#Remove label even if renaming was skipped:
	eachItem['labels'].remove(aLabel['id'])
	#Apply changes to local instance:
	api.items.get_by_id(eachItem['id']).update(content=taskName, labels=eachItem['labels'])
	if searchCompletedTasks == 2: api.items.get_by_id(eachItem['id']).update(is_deleted=0, in_history=0)
	updatedCount += 1

#Commit:
commitResult = api.commit()
print("{0} item{1} updated.".format(updatedCount, "" if updatedCount == 1 else "s" ))
if commitResult != None:
	for eachResultItem in commitResult['items']:
		print("* " + eachResultItem['content'])
