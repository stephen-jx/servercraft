"""Components API endpoints."""
from fastapi import APIRouter
from typing import Dict, List
from ...services.components import (
    list_components, get_component, get_categories,
    ComponentCategory, Component
)

router = APIRouter(prefix="/components", tags=["components"])


@router.get("")
async def list_all_components():
    """List all available components."""
    components = list_components()
    
    # Return flat list with category field
    items = []
    for comp in components:
        items.append({
            "name": comp.name,
            "display_name": comp.display_name,
            "category": comp.category.value,
            "description": comp.description,
            "default_version": comp.default_version,
            "versions": comp.versions,
            "ports": comp.ports,
            "icon": comp.icon,
            "dependencies": comp.dependencies,
        })
    
    return {
        "items": items,
        "categories": get_categories()
    }


@router.get("/categories")
async def list_categories():
    """List component categories."""
    return get_categories()


@router.get("/{component_name}")
async def get_component_details(component_name: str):
    """Get component details."""
    comp = get_component(component_name)
    if not comp:
        from fastapi import HTTPException
        raise HTTPException(404, f"Component not found: {component_name}")
    
    return {
        "name": comp.name,
        "display_name": comp.display_name,
        "category": comp.category.value,
        "description": comp.description,
        "default_version": comp.default_version,
        "versions": comp.versions,
        "supported_os": comp.supported_os,
        "options": [
            {
                "name": opt.name,
                "label": opt.label,
                "type": opt.type,
                "default": opt.default,
                "required": opt.required,
                "options": opt.options,
                "description": opt.description,
            }
            for opt in comp.options
        ],
        "dependencies": comp.dependencies,
        "ports": comp.ports,
        "icon": comp.icon,
    }


@router.get("/{component_name}/options")
async def get_component_options(component_name: str):
    """Get component installation options."""
    comp = get_component(component_name)
    if not comp:
        from fastapi import HTTPException
        raise HTTPException(404, f"Component not found: {component_name}")
    
    return {
        "component": comp.name,
        "options": [
            {
                "name": opt.name,
                "label": opt.label,
                "type": opt.type,
                "default": opt.default,
                "required": opt.required,
                "options": opt.options,
                "description": opt.description,
            }
            for opt in comp.options
        ]
    }