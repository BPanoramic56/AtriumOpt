import configparser

# CREATE OBJECT
config_file = configparser.ConfigParser()

# ADD SECTION
config_file["UserInformation"]={
    "Location":"localhost",
    "Name":"root",
    "Password":"Panoramic56"
    }

# SAVE CONFIG FILE
with open(r"configurations.ini", 'w') as configfileObj:
    config_file.write(configfileObj)
    configfileObj.flush()
    configfileObj.close()

print("Config file 'configurations.ini' created")

# PRINT FILE CONTENT
read_file = open("configurations.ini", "r")
content = read_file.read()
print("Content of the config file are:\n")
print(content)
read_file.flush()
read_file.close()