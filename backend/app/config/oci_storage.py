"""
Oracle Cloud Infrastructure (OCI) Object Storage Service
"""
import os
import uuid
from datetime import datetime, timedelta
from typing import BinaryIO
import oci
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger("app.storage")


class OCIStorageService:
    """Service for interacting with Oracle Cloud Object Storage"""
    
    _client: oci.object_storage.ObjectStorageClient | None = None
    
    @classmethod
    def get_client(cls) -> oci.object_storage.ObjectStorageClient:
        """Get or create OCI Object Storage client"""
        if cls._client is None:
            # Try config file first, fall back to instance principal
            try:
                config = oci.config.from_file(
                    file_location=os.path.expanduser(settings.oci_config_file),
                    profile_name=settings.oci_config_profile,
                )
                cls._client = oci.object_storage.ObjectStorageClient(config)
            except Exception:
                # Fall back to instance principal (for OCI compute instances)
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                cls._client = oci.object_storage.ObjectStorageClient(
                    config={}, signer=signer
                )
        return cls._client
    
    @classmethod
    def upload_file(
        cls,
        file_content: bytes | BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        folder: str = "uploads",
    ) -> dict:
        """
        Upload a file to OCI Object Storage.
        
        Args:
            file_content: File content as bytes or file-like object
            filename: Original filename
            content_type: MIME type
            folder: Folder path in bucket
            
        Returns:
            dict with object_name and url
        """
        client = cls.get_client()
        
        # Generate unique object name
        ext = os.path.splitext(filename)[1]
        unique_name = f"{uuid.uuid4().hex}{ext}"
        object_name = f"{folder}/{unique_name}"
        
        # Handle bytes vs file-like object
        if isinstance(file_content, bytes):
            body = file_content
        else:
            body = file_content.read()
        
        # Upload to OCI
        client.put_object(
            namespace_name=settings.oci_namespace,
            bucket_name=settings.oci_bucket_name,
            object_name=object_name,
            put_object_body=body,
            content_type=content_type,
            opc_meta={
                "original_filename": filename,
                "uploaded_at": datetime.utcnow().isoformat(),
            },
        )
        
        logger.info(f"Uploaded file to OCI: {object_name}")
        
        return {
            "object_name": object_name,
            "original_filename": filename,
            "url": cls.get_object_url(object_name),
        }
    
    @classmethod
    def get_object_url(cls, object_name: str, expiry_hours: int = 24) -> str:
        """
        Generate a pre-authenticated request (PAR) URL for an object.
        
        Args:
            object_name: Path to object in bucket
            expiry_hours: Hours until URL expires
            
        Returns:
            Pre-signed URL for object access
        """
        client = cls.get_client()
        
        # Create pre-authenticated request
        par_details = oci.object_storage.models.CreatePreauthenticatedRequestDetails(
            name=f"download-{uuid.uuid4().hex[:8]}",
            access_type="ObjectRead",
            object_name=object_name,
            time_expires=datetime.utcnow() + timedelta(hours=expiry_hours),
        )
        
        par = client.create_preauthenticated_request(
            namespace_name=settings.oci_namespace,
            bucket_name=settings.oci_bucket_name,
            create_preauthenticated_request_details=par_details,
        )
        
        # Build full URL
        base_url = f"https://objectstorage.{settings.oci_region}.oraclecloud.com"
        return f"{base_url}{par.data.access_uri}"
    
    @classmethod
    def download_file(cls, object_name: str) -> bytes:
        """Download a file from OCI Object Storage"""
        client = cls.get_client()
        
        response = client.get_object(
            namespace_name=settings.oci_namespace,
            bucket_name=settings.oci_bucket_name,
            object_name=object_name,
        )
        
        return response.data.content
    
    @classmethod
    def delete_file(cls, object_name: str) -> bool:
        """Delete a file from OCI Object Storage"""
        client = cls.get_client()
        
        try:
            client.delete_object(
                namespace_name=settings.oci_namespace,
                bucket_name=settings.oci_bucket_name,
                object_name=object_name,
            )
            logger.info(f"Deleted file from OCI: {object_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    @classmethod
    def list_files(cls, prefix: str = "") -> list[dict]:
        """List files in a folder"""
        client = cls.get_client()
        
        response = client.list_objects(
            namespace_name=settings.oci_namespace,
            bucket_name=settings.oci_bucket_name,
            prefix=prefix,
        )
        
        return [
            {
                "name": obj.name,
                "size": obj.size,
                "time_created": obj.time_created,
            }
            for obj in response.data.objects
        ]
