"""
Utility script to encrypt existing plaintext data in the database.

This script:
1. Backs up plaintext data
2. Encrypts PII fields (email, full_name)
3. Updates database records with encrypted values
4. Validates encryption/decryption

Usage:
    python -m app.utils.encrypt_existing_data --dry-run  # Preview changes
    python -m app.utils.encrypt_existing_data --encrypt  # Perform encryption
    python -m app.utils.encrypt_existing_data --verify   # Verify encryption

⚠️ IMPORTANT:
- Always backup your database before running this script
- Test in development environment first
- Use --dry-run to preview changes
"""

import argparse
import sys
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.utils.database import SessionLocal
from app.utils.encryption import get_encryption_service
from app.models.user import User

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataEncryptionMigration:
    """Handle encryption of existing plaintext data"""

    def __init__(self, db: Session):
        self.db = db
        self.encryption_service = get_encryption_service()
        self.stats = {
            'users_processed': 0,
            'users_encrypted': 0,
            'users_skipped': 0,
            'errors': 0
        }

    def is_encrypted(self, value: str) -> bool:
        """Check if a value is already encrypted"""
        if not value:
            return False
        # Fernet tokens start with 'gAAAAAB'
        return value.startswith('gAAAAAB')

    def encrypt_user_data(self, dry_run: bool = True) -> dict:
        """
        Encrypt user PII fields.

        Args:
            dry_run: If True, only preview changes without modifying data

        Returns:
            Statistics dictionary
        """
        logger.info(f"Starting user data encryption (dry_run={dry_run})...")

        users = self.db.query(User).all()
        logger.info(f"Found {len(users)} users to process")

        for user in users:
            try:
                self.stats['users_processed'] += 1
                needs_encryption = False

                # Check email
                if user.email and not self.is_encrypted(user.email):
                    logger.info(f"User {user.id} - Email needs encryption: {user.email}")
                    if not dry_run:
                        user.email = self.encryption_service.encrypt(user.email)
                    needs_encryption = True

                # Check full_name
                if user.full_name and not self.is_encrypted(user.full_name):
                    logger.info(f"User {user.id} - Full name needs encryption: {user.full_name}")
                    if not dry_run:
                        user.full_name = self.encryption_service.encrypt(user.full_name)
                    needs_encryption = True

                if needs_encryption:
                    self.stats['users_encrypted'] += 1
                    if not dry_run:
                        self.db.commit()
                        logger.info(f"✅ User {user.id} encrypted successfully")
                else:
                    self.stats['users_skipped'] += 1
                    logger.debug(f"⏭️  User {user.id} already encrypted")

            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"❌ Error encrypting user {user.id}: {e}")
                self.db.rollback()

        return self.stats

    def verify_encryption(self) -> dict:
        """
        Verify that encrypted data can be decrypted correctly.

        Returns:
            Verification statistics
        """
        logger.info("Verifying encrypted data...")

        verification_stats = {
            'total_users': 0,
            'encrypted_emails': 0,
            'encrypted_names': 0,
            'decryption_errors': 0,
            'unencrypted_found': 0
        }

        users = self.db.query(User).all()
        verification_stats['total_users'] = len(users)

        for user in users:
            # Check email
            if user.email:
                if self.is_encrypted(user.email):
                    verification_stats['encrypted_emails'] += 1
                    try:
                        decrypted = self.encryption_service.decrypt(user.email)
                        if decrypted:
                            logger.debug(f"✅ User {user.id} email decrypts successfully")
                        else:
                            verification_stats['decryption_errors'] += 1
                            logger.error(f"❌ User {user.id} email decryption failed")
                    except Exception as e:
                        verification_stats['decryption_errors'] += 1
                        logger.error(f"❌ User {user.id} email decryption error: {e}")
                else:
                    verification_stats['unencrypted_found'] += 1
                    logger.warning(f"⚠️  User {user.id} email is not encrypted: {user.email}")

            # Check full_name
            if user.full_name:
                if self.is_encrypted(user.full_name):
                    verification_stats['encrypted_names'] += 1
                    try:
                        decrypted = self.encryption_service.decrypt(user.full_name)
                        if decrypted:
                            logger.debug(f"✅ User {user.id} name decrypts successfully")
                        else:
                            verification_stats['decryption_errors'] += 1
                            logger.error(f"❌ User {user.id} name decryption failed")
                    except Exception as e:
                        verification_stats['decryption_errors'] += 1
                        logger.error(f"❌ User {user.id} name decryption error: {e}")
                else:
                    verification_stats['unencrypted_found'] += 1
                    logger.warning(f"⚠️  User {user.id} name is not encrypted: {user.full_name}")

        return verification_stats

    def create_backup(self, backup_file: str = None) -> str:
        """
        Create a backup of plaintext data before encryption.

        Args:
            backup_file: Optional backup file path

        Returns:
            Backup file path
        """
        if backup_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"/tmp/user_data_backup_{timestamp}.sql"

        logger.info(f"Creating backup at {backup_file}...")

        try:
            # Export user data
            users = self.db.query(User).all()

            with open(backup_file, 'w') as f:
                f.write(f"-- User Data Backup - {datetime.now()}\n")
                f.write(f"-- Total users: {len(users)}\n\n")

                for user in users:
                    f.write(f"-- User ID: {user.id}\n")
                    f.write(f"-- Username: {user.username}\n")
                    f.write(f"-- Email: {user.email}\n")
                    f.write(f"-- Full Name: {user.full_name}\n")
                    f.write(f"-- Role: {user.role}\n\n")

            logger.info(f"✅ Backup created successfully: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"❌ Backup creation failed: {e}")
            raise


def print_statistics(stats: dict, title: str):
    """Print statistics in a formatted way"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    for key, value in stats.items():
        key_formatted = key.replace('_', ' ').title()
        print(f"  {key_formatted:.<40} {value}")
    print(f"{'=' * 60}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Encrypt existing plaintext data in the database"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying data'
    )
    parser.add_argument(
        '--encrypt',
        action='store_true',
        help='Perform encryption (DANGEROUS - backup first!)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify encrypted data'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create backup only'
    )
    parser.add_argument(
        '--backup-file',
        type=str,
        help='Custom backup file path'
    )

    args = parser.parse_args()

    # Require at least one action
    if not any([args.dry_run, args.encrypt, args.verify, args.backup]):
        parser.print_help()
        sys.exit(1)

    # Get database session
    db = SessionLocal()

    try:
        migration = DataEncryptionMigration(db)

        # Create backup
        if args.backup or args.encrypt:
            print("\n🔐 Creating backup before encryption...")
            backup_file = migration.create_backup(args.backup_file)
            print(f"✅ Backup created: {backup_file}")
            print("⚠️  Store this backup securely!")

        # Dry run
        if args.dry_run:
            print("\n🔍 DRY RUN MODE - No changes will be made")
            stats = migration.encrypt_user_data(dry_run=True)
            print_statistics(stats, "Dry Run Results")

        # Perform encryption
        if args.encrypt:
            print("\n⚠️  WARNING: About to encrypt data!")
            print("   This will modify your database.")
            print("   Make sure you have a backup!")
            response = input("\nType 'yes' to continue: ")

            if response.lower() != 'yes':
                print("❌ Encryption cancelled")
                sys.exit(0)

            print("\n🔐 Encrypting data...")
            stats = migration.encrypt_user_data(dry_run=False)
            print_statistics(stats, "Encryption Results")

        # Verify encryption
        if args.verify:
            print("\n🔍 Verifying encryption...")
            verification_stats = migration.verify_encryption()
            print_statistics(verification_stats, "Verification Results")

            if verification_stats['decryption_errors'] > 0:
                print("❌ Verification failed! Some data cannot be decrypted.")
                sys.exit(1)
            elif verification_stats['unencrypted_found'] > 0:
                print("⚠️  Warning: Some unencrypted data found.")
            else:
                print("✅ All encrypted data verified successfully!")

    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
