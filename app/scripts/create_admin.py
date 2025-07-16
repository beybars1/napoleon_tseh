#!/usr/bin/env python3
"""
Script to create an admin user for the Cake CRM system
"""

import asyncio
import sys
from getpass import getpass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Add the parent directory to the path so we can import app modules
sys.path.append('/home/beybars/Desktop/beybars/projects/napoleon_tseh')

from app.core.database import async_engine
from app.models.user import User, UserRole
from app.core.security import get_password_hash


async def create_admin_user():
    """Create an admin user interactively"""
    
    print("=== Create Admin User ===")
    print()
    
    # Get user input
    username = input("Enter admin username: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        return
    
    email = input("Enter admin email: ").strip()
    if not email:
        print("Error: Email cannot be empty")
        return
    
    full_name = input("Enter admin full name: ").strip()
    if not full_name:
        print("Error: Full name cannot be empty")
        return
    
    password = getpass("Enter admin password: ")
    if not password:
        print("Error: Password cannot be empty")
        return
    
    password_confirm = getpass("Confirm admin password: ")
    if password != password_confirm:
        print("Error: Passwords do not match")
        return
    
    # Create database session
    async with AsyncSession(async_engine) as session:
        try:
            # Check if user already exists
            existing_user = await session.execute(
                select(User).where(
                    (User.username == username) | (User.email == email)
                )
            )
            if existing_user.scalar_one_or_none():
                print(f"Error: User with username '{username}' or email '{email}' already exists")
                return
            
            # Create admin user
            admin_user = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(password),
                role=UserRole.ADMIN,
                is_active=True
            )
            
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            print(f"\n✅ Admin user created successfully!")
            print(f"Username: {admin_user.username}")
            print(f"Email: {admin_user.email}")
            print(f"Full Name: {admin_user.full_name}")
            print(f"Role: {admin_user.role.value}")
            print(f"User ID: {admin_user.id}")
            
        except Exception as e:
            print(f"Error creating admin user: {e}")
            await session.rollback()
        finally:
            await session.close()


async def create_default_admin():
    """Create a default admin user with predefined credentials"""
    
    print("=== Creating Default Admin User ===")
    
    # Default admin credentials
    username = "admin"
    email = "admin@napoleontseh.com"
    full_name = "System Administrator"
    password = "admin123"  # Change this in production!
    
    # Create database session
    async with AsyncSession(async_engine) as session:
        try:
            # Check if admin user already exists
            existing_admin = await session.execute(
                select(User).where(User.role == UserRole.ADMIN)
            )
            if existing_admin.scalar_one_or_none():
                print("Admin user already exists!")
                return
            
            # Create default admin user
            admin_user = User(
                username=username,
                email=email,
                full_name=full_name,
                hashed_password=get_password_hash(password),
                role=UserRole.ADMIN,
                is_active=True
            )
            
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)
            
            print(f"\n✅ Default admin user created successfully!")
            print(f"Username: {admin_user.username}")
            print(f"Email: {admin_user.email}")
            print(f"Password: {password}")
            print(f"⚠️  Please change the password after first login!")
            
        except Exception as e:
            print(f"Error creating default admin user: {e}")
            await session.rollback()
        finally:
            await session.close()


def main():
    """Main function to run the admin creation script"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--default":
        # Create default admin
        asyncio.run(create_default_admin())
    else:
        # Create admin interactively
        asyncio.run(create_admin_user())


if __name__ == "__main__":
    main() 