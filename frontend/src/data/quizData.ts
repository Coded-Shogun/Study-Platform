export interface QuizQuestion {
  id: string
  domain: string
  question: string
  options: string[]
  correctAnswer: string
  explanation: string
}

export const quizQuestions: QuizQuestion[] = [
  // Cloud Architecture & Design
  {
    id: '1',
    domain: 'Cloud Architecture & Design',
    question: 'What is the primary benefit of using a multi-cloud strategy?',
    options: [
      'Reduced costs',
      'Vendor lock-in avoidance',
      'Simplified management',
      'Faster deployment'
    ],
    correctAnswer: 'Vendor lock-in avoidance',
    explanation: 'Multi-cloud strategies primarily help organizations avoid vendor lock-in by distributing workloads across multiple cloud providers, giving them flexibility and negotiating power.'
  },
  {
    id: '2',
    domain: 'Cloud Architecture & Design',
    question: 'Which cloud service model provides the most control over the underlying infrastructure?',
    options: [
      'Software as a Service (SaaS)',
      'Platform as a Service (PaaS)',
      'Infrastructure as a Service (IaaS)',
      'Function as a Service (FaaS)'
    ],
    correctAnswer: 'Infrastructure as a Service (IaaS)',
    explanation: 'IaaS provides the most control as you manage the operating system, applications, and data while the provider manages the physical infrastructure.'
  },
  {
    id: '3',
    domain: 'Cloud Architecture & Design',
    question: 'What is horizontal scaling?',
    options: [
      'Adding more powerful hardware to existing servers',
      'Adding more servers to distribute the load',
      'Increasing network bandwidth',
      'Upgrading storage capacity'
    ],
    correctAnswer: 'Adding more servers to distribute the load',
    explanation: 'Horizontal scaling (scaling out) involves adding more servers to distribute the workload, rather than upgrading existing hardware (vertical scaling).'
  },
  {
    id: '4',
    domain: 'Cloud Architecture & Design',
    question: 'Which architectural pattern is best for handling unpredictable workloads?',
    options: [
      'Monolithic architecture',
      'Auto-scaling architecture',
      'Static provisioning',
      'Manual scaling'
    ],
    correctAnswer: 'Auto-scaling architecture',
    explanation: 'Auto-scaling automatically adjusts resources based on demand, making it ideal for unpredictable workloads by scaling up during high demand and down during low demand.'
  },
  {
    id: '5',
    domain: 'Cloud Architecture & Design',
    question: 'What is the purpose of a load balancer in cloud architecture?',
    options: [
      'Store application data',
      'Distribute traffic across multiple servers',
      'Monitor system performance',
      'Encrypt data in transit'
    ],
    correctAnswer: 'Distribute traffic across multiple servers',
    explanation: 'Load balancers distribute incoming network traffic across multiple servers to ensure no single server bears too much load, improving availability and reliability.'
  },

  // Security
  {
    id: '6',
    domain: 'Security',
    question: 'What is the principle of least privilege?',
    options: [
      'Give users maximum access to simplify management',
      'Grant users only the minimum access needed to perform their jobs',
      'Remove all access restrictions',
      'Provide administrative access to all users'
    ],
    correctAnswer: 'Grant users only the minimum access needed to perform their jobs',
    explanation: 'The principle of least privilege states that users should be granted only the minimum levels of access needed to complete their job functions, reducing security risks.'
  },
  {
    id: '7',
    domain: 'Security',
    question: 'Which encryption method protects data in transit?',
    options: [
      'TLS/SSL',
      'AES encryption',
      'Hash functions',
      'Filesystem encryption'
    ],
    correctAnswer: 'TLS/SSL',
    explanation: 'TLS (Transport Layer Security) and SSL (Secure Sockets Layer) are cryptographic protocols designed to provide secure communication over networks, protecting data in transit.'
  },
  {
    id: '8',
    domain: 'Security',
    question: 'What is a DDoS attack?',
    options: [
      'Data theft from servers',
      'Overwhelming a system with traffic to make it unavailable',
      'Unauthorized access to databases',
      'Malware infection'
    ],
    correctAnswer: 'Overwhelming a system with traffic to make it unavailable',
    explanation: 'A Distributed Denial of Service (DDoS) attack attempts to make a service unavailable by overwhelming it with traffic from multiple sources.'
  },
  {
    id: '9',
    domain: 'Security',
    question: 'What is the purpose of IAM (Identity and Access Management)?',
    options: [
      'Monitor network traffic',
      'Control who can access resources and what they can do',
      'Encrypt data at rest',
      'Backup user data'
    ],
    correctAnswer: 'Control who can access resources and what they can do',
    explanation: 'IAM enables you to manage access to cloud resources by controlling authentication (who can sign in) and authorization (what permissions they have).'
  },
  {
    id: '10',
    domain: 'Security',
    question: 'What is multi-factor authentication (MFA)?',
    options: [
      'Using multiple passwords',
      'Requiring two or more verification methods to access a resource',
      'Having multiple user accounts',
      'Using different browsers for access'
    ],
    correctAnswer: 'Requiring two or more verification methods to access a resource',
    explanation: 'MFA enhances security by requiring users to provide two or more verification factors to gain access, such as something they know (password) and something they have (phone).'
  },

  // Deployment
  {
    id: '11',
    domain: 'Deployment',
    question: 'What is Infrastructure as Code (IaC)?',
    options: [
      'Writing application code in the cloud',
      'Managing infrastructure through machine-readable files',
      'Coding directly on servers',
      'Cloud provider APIs'
    ],
    correctAnswer: 'Managing infrastructure through machine-readable files',
    explanation: 'IaC is the practice of managing and provisioning infrastructure through code and configuration files rather than manual processes, enabling automation and version control.'
  },
  {
    id: '12',
    domain: 'Deployment',
    question: 'Which deployment strategy allows gradual rollout to users?',
    options: [
      'Big bang deployment',
      'Blue-green deployment',
      'Canary deployment',
      'Rollback deployment'
    ],
    correctAnswer: 'Canary deployment',
    explanation: 'Canary deployment gradually rolls out changes to a small subset of users before deploying to the entire infrastructure, allowing for testing in production with minimal risk.'
  },
  {
    id: '13',
    domain: 'Deployment',
    question: 'What is a container orchestration platform?',
    options: [
      'A tool for creating containers',
      'A system for managing containerized applications at scale',
      'A container image registry',
      'A virtualization platform'
    ],
    correctAnswer: 'A system for managing containerized applications at scale',
    explanation: 'Container orchestration platforms like Kubernetes automate deployment, scaling, and management of containerized applications across clusters of hosts.'
  },
  {
    id: '14',
    domain: 'Deployment',
    question: 'What is continuous integration (CI)?',
    options: [
      'Constantly monitoring applications',
      'Frequently merging code changes and automatically testing them',
      'Continuous deployment to production',
      'Real-time data integration'
    ],
    correctAnswer: 'Frequently merging code changes and automatically testing them',
    explanation: 'CI is a practice where developers frequently merge their code changes into a shared repository, with automated builds and tests to detect integration issues early.'
  },
  {
    id: '15',
    domain: 'Deployment',
    question: 'What is the purpose of a staging environment?',
    options: [
      'Store backup data',
      'Test changes before deploying to production',
      'Monitor production systems',
      'Train new users'
    ],
    correctAnswer: 'Test changes before deploying to production',
    explanation: 'A staging environment replicates the production environment and is used to test changes, updates, and new features before deploying them to production users.'
  },

  // Operations & Support
  {
    id: '16',
    domain: 'Operations & Support',
    question: 'What is the purpose of monitoring in cloud operations?',
    options: [
      'Backup data regularly',
      'Track performance and detect issues',
      'Deploy applications',
      'Manage user accounts'
    ],
    correctAnswer: 'Track performance and detect issues',
    explanation: 'Monitoring continuously tracks system performance, resource utilization, and application health to detect issues proactively and ensure optimal operation.'
  },
  {
    id: '17',
    domain: 'Operations & Support',
    question: 'What is a Service Level Agreement (SLA)?',
    options: [
      'A contract defining expected service levels and penalties',
      'A software license agreement',
      'A security policy document',
      'A deployment checklist'
    ],
    correctAnswer: 'A contract defining expected service levels and penalties',
    explanation: 'An SLA is a commitment between a service provider and customer that defines the level of service expected, including uptime guarantees and remedies for non-compliance.'
  },
  {
    id: '18',
    domain: 'Operations & Support',
    question: 'What does RPO (Recovery Point Objective) measure?',
    options: [
      'How long it takes to recover from an outage',
      'The maximum acceptable amount of data loss',
      'Server response time',
      'Network bandwidth'
    ],
    correctAnswer: 'The maximum acceptable amount of data loss',
    explanation: 'RPO defines the maximum acceptable amount of data loss measured in time. For example, an RPO of 1 hour means you can lose at most 1 hour of data.'
  },
  {
    id: '19',
    domain: 'Operations & Support',
    question: 'What is the difference between RTO and RPO?',
    options: [
      'There is no difference',
      'RTO is recovery time, RPO is acceptable data loss',
      'RTO is for data, RPO is for systems',
      'RTO is longer than RPO'
    ],
    correctAnswer: 'RTO is recovery time, RPO is acceptable data loss',
    explanation: 'RTO (Recovery Time Objective) is the maximum acceptable time to restore service after a disruption. RPO is the maximum acceptable data loss measured in time.'
  },
  {
    id: '20',
    domain: 'Operations & Support',
    question: 'What is log aggregation?',
    options: [
      'Deleting old logs',
      'Collecting logs from multiple sources into a central location',
      'Compressing log files',
      'Encrypting log data'
    ],
    correctAnswer: 'Collecting logs from multiple sources into a central location',
    explanation: 'Log aggregation collects log data from multiple systems and applications into a centralized location for easier searching, analysis, and monitoring.'
  },

  // Troubleshooting
  {
    id: '21',
    domain: 'Troubleshooting',
    question: 'What is the first step in troubleshooting a performance issue?',
    options: [
      'Restart all services',
      'Gather information and identify symptoms',
      'Apply patches',
      'Scale up resources'
    ],
    correctAnswer: 'Gather information and identify symptoms',
    explanation: 'The first step in any troubleshooting process is to gather information about the problem, identify symptoms, and understand the scope before attempting solutions.'
  },
  {
    id: '22',
    domain: 'Troubleshooting',
    question: 'What tool would you use to test network connectivity?',
    options: [
      'grep',
      'ping',
      'chmod',
      'tar'
    ],
    correctAnswer: 'ping',
    explanation: 'Ping is a network utility that tests connectivity between two hosts by sending ICMP echo request packets and measuring response time.'
  },
  {
    id: '23',
    domain: 'Troubleshooting',
    question: 'What does a 503 HTTP status code indicate?',
    options: [
      'Page not found',
      'Unauthorized access',
      'Service unavailable',
      'Internal server error'
    ],
    correctAnswer: 'Service unavailable',
    explanation: 'HTTP 503 Service Unavailable indicates that the server is temporarily unable to handle the request, often due to maintenance or overload.'
  },
  {
    id: '24',
    domain: 'Troubleshooting',
    question: 'What is the purpose of a packet capture tool like tcpdump?',
    options: [
      'Monitor CPU usage',
      'Analyze network traffic',
      'Test disk performance',
      'Manage user permissions'
    ],
    correctAnswer: 'Analyze network traffic',
    explanation: 'Packet capture tools like tcpdump capture and analyze network packets, helping diagnose network issues by examining the actual data being transmitted.'
  },
  {
    id: '25',
    domain: 'Troubleshooting',
    question: 'What indicates high CPU usage might be causing performance issues?',
    options: [
      'Low network throughput',
      'Slow response times and high load average',
      'Disk space warnings',
      'Memory leaks'
    ],
    correctAnswer: 'Slow response times and high load average',
    explanation: 'High CPU usage typically manifests as slow application response times and elevated load averages, indicating the system is spending too much time processing tasks.'
  },

  // Additional Cloud Architecture Questions
  {
    id: '26',
    domain: 'Cloud Architecture & Design',
    question: 'What is serverless computing?',
    options: [
      'Computing without any servers',
      'A model where the cloud provider manages servers and you only pay for execution',
      'Running applications on local machines',
      'Using virtual machines'
    ],
    correctAnswer: 'A model where the cloud provider manages servers and you only pay for execution',
    explanation: 'Serverless computing abstracts server management from developers. You deploy code and the provider handles infrastructure, scaling, and maintenance, charging only for actual execution time.'
  },
  {
    id: '27',
    domain: 'Cloud Architecture & Design',
    question: 'What is a Content Delivery Network (CDN)?',
    options: [
      'A database system',
      'A network of distributed servers that deliver content based on geographic location',
      'A security firewall',
      'A backup solution'
    ],
    correctAnswer: 'A network of distributed servers that deliver content based on geographic location',
    explanation: 'CDNs distribute content across geographically dispersed servers to reduce latency and improve performance by serving content from locations closer to users.'
  },
  {
    id: '28',
    domain: 'Cloud Architecture & Design',
    question: 'What is the purpose of a Virtual Private Cloud (VPC)?',
    options: [
      'Provide a private cloud environment',
      'Create an isolated network within a public cloud',
      'Store private data',
      'Enable VPN connections'
    ],
    correctAnswer: 'Create an isolated network within a public cloud',
    explanation: 'A VPC provides an isolated virtual network within a public cloud, giving you control over IP address ranges, subnets, routing tables, and network gateways.'
  },
  {
    id: '29',
    domain: 'Security',
    question: 'What is encryption at rest?',
    options: [
      'Encrypting data during transmission',
      'Encrypting data stored on disk or in databases',
      'Encrypting network packets',
      'Encrypting backup data only'
    ],
    correctAnswer: 'Encrypting data stored on disk or in databases',
    explanation: 'Encryption at rest protects data stored on physical media (disks, databases, etc.) by encrypting it so unauthorized users cannot read it even if they gain physical access.'
  },
  {
    id: '30',
    domain: 'Security',
    question: 'What is a security group in cloud computing?',
    options: [
      'A group of security administrators',
      'A virtual firewall controlling inbound and outbound traffic',
      'A collection of security policies',
      'An authentication service'
    ],
    correctAnswer: 'A virtual firewall controlling inbound and outbound traffic',
    explanation: 'Security groups act as virtual firewalls that control inbound and outbound traffic to cloud resources using rules based on protocols, ports, and IP addresses.'
  }
]
