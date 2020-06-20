duplocli


# duplo-shell container setup

1. Create a new service in **default** tenant
    1. Name - **duplo-shell**
    2. Docker Image - **duplocloud/shell:terraform_kubectl_v3** (For new change build a new image and update version)
    3. Environment Variables
        {
            "AWS_ACCESS_KEY_ID": "**READ_ONLY_USER ACCESS KEY ID**",
            "AWS_SECRET_ACCESS_KEY": "**READ_ONLY_USER ACCESS SECRET**",
            "AWS_DEFAULT_REGION": "**AWS_REGION**",
            "EXPORT_BUCKET": "**S3 Bukcet to export terraform scripts**",
            "FLASK_APP_SECRET": "**Random string more than 15 chars. Flask using this to generate token**",
            "DUPLO_AUTH_URL": "**DUPLO Portal url of current env**https://<ENV_NAME>.duplocloud.net"
        }
    4. Add Load Balancer
        - LB Type - **Classic**
        - Container port - **80**
        - External port - **443**
        - Visibility - **Public**
        - Application Mode - **Docker**
        - Backend protocol - **tcp**
        - Certificate - **Select external DNS domain certificate**

Once this service is created. Duplo UI code will automatically discover this shell container and enabled both Terraform export and kubectl functionalities.