"""Base repository with common CRUD operations for all models."""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel


# Type variables for generic repository
ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class PaginationResult(Generic[ModelType]):
    """Container for paginated results with metadata."""
    
    def __init__(
        self,
        items: List[ModelType],
        total: int,
        page: int,
        page_size: int
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pagination result to dictionary."""
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages
        }


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base repository providing common CRUD operations for all models.
    
    This class implements:
    - Create: Insert new records
    - Read: Get by ID, list with pagination
    - Update: Update existing records
    - Delete: Hard delete and soft delete
    - Pagination: Support for paginated queries
    
    Type Parameters:
        ModelType: SQLAlchemy model class
        CreateSchemaType: Pydantic schema for creation
        UpdateSchemaType: Pydantic schema for updates
    """
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        """
        Initialize repository with model and database session.
        
        Args:
            model: SQLAlchemy model class
            db: Async database session
        """
        self.model = model
        self.db = db
    
    async def create(self, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """
        Create a new record in the database.
        
        Args:
            obj_in: Pydantic schema with creation data or dict
            **kwargs: Additional fields to set (e.g., created_by)
        
        Returns:
            Created model instance
        """
        # Convert Pydantic model to dict, or use dict directly
        if isinstance(obj_in, dict):
            obj_data = obj_in.copy()
        elif hasattr(obj_in, 'model_dump'):
            obj_data = obj_in.model_dump()
        elif hasattr(obj_in, 'dict'):
            obj_data = obj_in.dict()
        else:
            obj_data = dict(obj_in)
        
        # Convert HttpUrl objects to strings (Pydantic v2 compatibility)
        for key, value in obj_data.items():
            if hasattr(value, '__class__') and value.__class__.__name__ == 'Url':
                obj_data[key] = str(value)
        
        # Merge with additional kwargs
        obj_data.update(kwargs)
        
        # Create model instance
        db_obj = self.model(**obj_data)
        
        # Add to session and flush to get ID
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        
        return db_obj
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """
        Get a record by its ID.
        
        Args:
            id: UUID of the record
        
        Returns:
            Model instance or None if not found
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[Any]] = None
    ) -> List[ModelType]:
        """
        List records with optional filtering and ordering.
        
        Args:
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return
            filters: Dictionary of field:value filters
            order_by: List of SQLAlchemy order_by clauses
        
        Returns:
            List of model instances
        """
        query = select(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)
        
        # Apply ordering
        if order_by:
            query = query.order_by(*order_by)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def list_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[Any]] = None
    ) -> PaginationResult[ModelType]:
        """
        List records with pagination metadata.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Dictionary of field:value filters
            order_by: List of SQLAlchemy order_by clauses
        
        Returns:
            PaginationResult with items and metadata
        """
        # Build base query
        query = select(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply ordering
        if order_by:
            query = query.order_by(*order_by)
        
        # Apply pagination
        skip = (page - 1) * page_size
        query = query.offset(skip).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        
        return PaginationResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
    
    async def update(
        self,
        id: UUID,
        obj_in: UpdateSchemaType,
        **kwargs
    ) -> Optional[ModelType]:
        """
        Update an existing record.
        
        Args:
            id: UUID of the record to update
            obj_in: Pydantic schema with update data
            **kwargs: Additional fields to set (e.g., updated_by)
        
        Returns:
            Updated model instance or None if not found
        """
        # Get existing record
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None
        
        # Convert Pydantic model to dict, or use dict directly
        if isinstance(obj_in, dict):
            update_data = obj_in.copy()
        elif hasattr(obj_in, 'model_dump'):
            update_data = obj_in.model_dump(exclude_unset=True)
        elif hasattr(obj_in, 'dict'):
            update_data = obj_in.dict(exclude_unset=True)
        else:
            update_data = dict(obj_in)
        
        # Convert HttpUrl objects to strings (Pydantic v2 compatibility)
        for key, value in update_data.items():
            if hasattr(value, '__class__') and value.__class__.__name__ == 'Url':
                update_data[key] = str(value)
        
        # Merge with additional kwargs
        update_data.update(kwargs)
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # Flush changes
        await self.db.flush()
        await self.db.refresh(db_obj)
        
        return db_obj
    
    async def delete(self, id: UUID) -> bool:
        """
        Hard delete a record from the database.
        
        Args:
            id: UUID of the record to delete
        
        Returns:
            True if deleted, False if not found
        """
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0
    
    async def soft_delete(self, id: UUID, **kwargs) -> Optional[ModelType]:
        """
        Soft delete a record by setting its status to 'deleted'.
        
        This method assumes the model has a 'status' field.
        
        Args:
            id: UUID of the record to soft delete
            **kwargs: Additional fields to set (e.g., deleted_by)
        
        Returns:
            Updated model instance or None if not found
        """
        # Check if model has status field
        if not hasattr(self.model, 'status'):
            raise AttributeError(f"{self.model.__name__} does not have a 'status' field for soft delete")
        
        # Get existing record
        db_obj = await self.get_by_id(id)
        if not db_obj:
            return None
        
        # Set status to deleted
        db_obj.status = 'deleted'
        
        # Set additional fields
        for field, value in kwargs.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        # Flush changes
        await self.db.flush()
        await self.db.refresh(db_obj)
        
        return db_obj
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records matching the given filters.
        
        Args:
            filters: Dictionary of field:value filters
        
        Returns:
            Number of matching records
        """
        query = select(func.count()).select_from(self.model)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field) and value is not None:
                    query = query.where(getattr(self.model, field) == value)
        
        result = await self.db.execute(query)
        return result.scalar_one()
    
    async def exists(self, id: UUID) -> bool:
        """
        Check if a record exists by ID.
        
        Args:
            id: UUID of the record
        
        Returns:
            True if exists, False otherwise
        """
        result = await self.db.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return result.scalar_one() > 0
