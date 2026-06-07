in this repo i have got a project I need to transform. Right now it is
a static webpage of an ERP system. I need to change it to a dynamic
website.

I want to use AWS. I need the cheapest solution, preferably using just
free tier. The architecture I was thinking about is following

Internet
    │
    ▼
EC2 Ubuntu Server
├── Nginx
├── Django/FastAPI
└── PostgreSQL

Everything on 1 tiny EC2 instance. PostgreSQL needs to be installed on this server. For Authentication I want to use AWS Cognito. For infrastructure code I want to use Terraform. First please generate Terraform code to create the EC2 instance, install nginx, Django env, posgresql. Create infrastructure for the main AWS setup - network, Coginto setup, first admin IAM role, open ports so calls can be made to the server. Document everything, create documentation for each terraform module. Make terraform modules easy to move to a different aws account.

In the next step, modify the index.html page to Django. Scan the page and create python code and PostgreSQL tables for every module on the page - dashboard, purchases, sales, finance, stock. User, once he registers himself, will have his own settings configuration (page settings). Again, document everything.

Keep infrastructure code and business logic separate. Make the infrastructure code easy to migrate to a different aws account.