# Introduction
Scientific publications are continuously loaded to Amazon S3 and processed with Apache Kafka to create an output topic with word counts of the text corpus.
In this mini project, a data streaming pipeline is built with Apache Kafka and Faust to perform the word counting. Faust is a stream processing library, porting the ideas from Kafka Streams to Python as described by its owners.

Additionally, in order to take care of default max message size in Kafka for large text files greater than 1 MB; we’ll leverage on another python library from Amazon, Boto 3 with capabilities of reading objects in S3 transparently and feed to Faust application agents.

![Image](Screenshots/Flowchart.PNG?raw=true "Flowchart")

The Python Kafka producer also known as the Faust Application or Worker sits in the EC2 instance and interacts with the S3 bucket and the Kafka Cluster to complete the pipeline as shown in fig 1. Faust relies heavily on the newly Python asyncio and uses Apache Kafka as a message broker.



# Description

The Infrastructure that is used in this project is bundled as code with AWS CloudFormation. The resources created consist of a multi broker Serverless Amazon Managed Streaming for Apache Kafka (Amazon MSK) Cluster with an EC2 instance serving as the client to connect to the brokers as well as an S3 bucket. Specifically 3 brokers will be created and distributed evenly across 3 availability zones. 

![Image](Screenshots/Overview.PNG?raw=true "Overview")
 
It is worth noting that, almost every service in AWS uses the concept of ‘Least Privileges’ which basically says that a user or another AWS service cannot access other services unless granted permission and this is achieved by Roles and Policies among services in AWS. Therefore the EC2 being the backbone of the pipeline is granted permissions to access both the MSK cluster and S3 by assigning it a role with attach policies. The AWS account user will also require Access Keys to programmatically access resources (S3) through the boto 3 API. 
 

# Implementation
## Step 1: Dependencies
All the dependencies, be it access control or software have been taken care of in the CloudFormation code.  
### AWS - Related
-	AWS Account
-	EC2 KeyPairs 
-	Access key ID / Secret access key - Rename .env.example as .env and set the values of the keys
-	AWS MSK
-	Role and Policy access to access S3 and MSK Cluster 
-	Inbound Security Group Rules to access MSK and EC2 instance remotely 
### Non AWS Related
-	Python 3.7
-	Faust 1.0
-	Confluent-Kafka
-   kafka_2.12-2.2.1

##  Step 2: Create – Access Keys 
In the IAM console click on <b>Manage Security Credentials</b>

![Image](Screenshots/ACCESSKEY1.PNG?raw=true "ACCESSKEY1")
 
Click on <b>Create New Access Key</b> and then <b>Download Key File</b>
 


## Step 3: Create - EC2 KeyPairs 
In the EC2 <b>Key pairs page</b> click on <b>Create key pair</b> and provide a <b>name</b> and <b>file format.</b> 

Now click on <b>Create key pair</b> and MSKkeyPair is downloaded automatically. 

![Image](Screenshots/MSKKeyPair.PNG?raw=true "MSKKeyPair")


## Step 4: Deploying the MSK Cluster + S3 Bucket
In the AWS console - <b>Services</b> go to <b>CloudFormation</b> and then click <b>Create stack</b>

![Image](Screenshots/CF1.PNG?raw=true "CF1")
 
Select the location of the CloudFormation document and click <b>Next.</b>

![Image](Screenshots/CF2.PNG?raw=true "CF2")
 
Provide a name and select the KeyName created in step 3

![Image](Screenshots/CF3.PNG?raw=true "CF3")
 
Optionally add a tag Name and Value

![Image](Screenshots/CF4.PNG?raw=true "CF4")

Acknowledge and <b>Create Stack</b>

![Image](Screenshots/CF5.PNG?raw=true "CF5")


 
When start creation is done, all resources status will show as <b>CREATE_COMPLETE</b>

![Image](Screenshots/CF6.PNG?raw=true "CF6")

Everything is now set to go  :smile:




# Running and Testing
To run the producer, start the Kafka cluster. SSH into the Kafka Client Machine using the credentials obtained in Step 3 and the public IP of the EC2 instance that came with the Kafka Cluster. The screenshot given shows how to obtain the public IP address.

 ![Image](Screenshots/PublicIP.PNG?raw=true "PublicIP")

### Starting  Zookeeper:
```bash
cd kafka/kafka_2.12-2.2.1
bin/zookeeper-server-start.sh config/zookeeper.properties
```

### Starting Kafka Server:
```bash
cd kafka/kafka_2.12-2.2.1  
bin/kafka-server-start.sh config/server.properties
```

### Starting the producer and Consumer:

Upload the wordcount.py to the /home/ec2-user directory. Three files with different names but same content are uploaded to S3 in turns and  the word counts in each round is observed through the Faust app tables and the Output Topic in Kafka through the Kafka Console Consumer. The worker is built with a task timer of 1s. That is to say, the worker listens for the presence of new objects in the S3 bucket every second. 

<b><i>Watch Out!</i></b>

1- Run the Faust Application with the following command with an empty S3 bucket state in the /home/ec2-user directory:
```bash
faust -A wordcount worker -l info
```

 ![Image](Screenshots/P1.PNG?raw=true "P1")

The screenshot shows worker in a waiting state. Please note that by default Faust combines the app-id and table name and a suffix changelog to represent the name of the output topic sent to Kafka. In this example the console consumer consumes from word-count-word_counts-changelog.

2- Run Kafka Console Consumer in another window with: 
```bash
cd kafka/kafka_2.12-2.2.1  
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic word-count-word_counts-changelog --from-beginning --property print.key=true --property print.value=true
```

3- Put the Console Consumer window to the right of the Producer and Upload file A1.headed.txt to the S3 bucket. 

 ![Image](Screenshots/P2.PNG?raw=true "P2")
 
4- Next Upload A2.headed.txt .

 ![Image](Screenshots/P3.PNG?raw=true "P3")
 
5- Finally A3.headed.txt
 
  ![Image](Screenshots/P4.PNG?raw=true "P4")

# Conclusion
The last but two words in the console consumer “the” and “star” appears one hundred and twentieth and one times respectively in the first instance of file upload to S3, accumulating to three hundred and sixty and three respectively on the third upload indicating the Word Count App is working as expected.
