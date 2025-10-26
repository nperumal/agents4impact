"""Maps generation agent for geospatial data and visualization."""

from typing import Any, Dict, List
import json
import googlemaps
from datetime import datetime
from .base_agent import BaseAgent
from config import Config


class MapsAgent(BaseAgent):
    """Agent for generating maps and geospatial information."""

    def __init__(self):
        """Initialize the maps agent."""
        super().__init__(
            name="Maps Agent",
            description="Specialized agent for generating maps and providing geospatial information",
            instructions="""You are a maps and geospatial expert agent. Your role is to:
1. Generate map visualizations based on location data
2. Provide directions and route information
3. Geocode addresses to coordinates
4. Reverse geocode coordinates to addresses
5. Calculate distances and travel times
6. Find nearby places and points of interest
7. Create static map URLs for embedding

Always provide accurate location information and handle ambiguous locations appropriately.
Use appropriate zoom levels and map types for different use cases.""",
        )

        self.api_key = Config.MAPS_API_KEY
        # Initialize Google Maps client
        if self.api_key:
            self.gmaps = googlemaps.Client(key=self.api_key)
        else:
            self.gmaps = None
            print("Warning: MAPS_API_KEY not configured. Using mock implementations.")

    def get_tools(self) -> List[Dict[str, Any]]:
        """Get maps-specific tools."""
        return [
            {
                "name": "geocode",
                "description": "Convert an address to geographic coordinates",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "address": {
                            "type": "string",
                            "description": "The address to geocode",
                        }
                    },
                    "required": ["address"],
                },
            },
            {
                "name": "reverse_geocode",
                "description": "Convert coordinates to an address",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "Latitude coordinate",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude coordinate",
                        },
                    },
                    "required": ["latitude", "longitude"],
                },
            },
            {
                "name": "get_directions",
                "description": "Get directions between two locations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Starting location (address or coordinates)",
                        },
                        "destination": {
                            "type": "string",
                            "description": "Ending location (address or coordinates)",
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["driving", "walking", "bicycling", "transit"],
                            "description": "Travel mode",
                            "default": "driving",
                        },
                    },
                    "required": ["origin", "destination"],
                },
            },
            {
                "name": "calculate_distance",
                "description": "Calculate distance and duration between locations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "origins": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of origin locations",
                        },
                        "destinations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of destination locations",
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["driving", "walking", "bicycling", "transit"],
                            "description": "Travel mode",
                            "default": "driving",
                        },
                    },
                    "required": ["origins", "destinations"],
                },
            },
            {
                "name": "find_nearby_places",
                "description": "Find places near a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "Center location for search",
                        },
                        "place_type": {
                            "type": "string",
                            "description": "Type of place to find (e.g., restaurant, hotel, gas_station)",
                        },
                        "radius": {
                            "type": "number",
                            "description": "Search radius in meters (default: 1000)",
                            "default": 1000,
                        },
                    },
                    "required": ["location"],
                },
            },
            {
                "name": "generate_static_map",
                "description": "Generate a static map URL for embedding",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "center": {
                            "type": "string",
                            "description": "Center location (address or coordinates)",
                        },
                        "zoom": {
                            "type": "integer",
                            "description": "Zoom level (0-21)",
                            "default": 13,
                        },
                        "size": {
                            "type": "string",
                            "description": "Image size (e.g., '600x400')",
                            "default": "600x400",
                        },
                        "markers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of marker locations",
                        },
                    },
                    "required": ["center"],
                },
            },
        ]

    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute maps tools."""
        try:
            if tool_name == "geocode":
                return self._geocode(parameters["address"])

            elif tool_name == "reverse_geocode":
                return self._reverse_geocode(
                    parameters["latitude"], parameters["longitude"]
                )

            elif tool_name == "get_directions":
                return self._get_directions(
                    parameters["origin"],
                    parameters["destination"],
                    parameters.get("mode", "driving"),
                )

            elif tool_name == "calculate_distance":
                return self._calculate_distance(
                    parameters["origins"],
                    parameters["destinations"],
                    parameters.get("mode", "driving"),
                )

            elif tool_name == "find_nearby_places":
                return self._find_nearby_places(
                    parameters["location"],
                    parameters.get("place_type"),
                    parameters.get("radius", 1000),
                )

            elif tool_name == "generate_static_map":
                return self._generate_static_map(parameters)

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"error": str(e)}

    def _geocode(self, address: str) -> Dict[str, Any]:
        """Geocode an address to coordinates."""
        if not self.gmaps:
            # Fallback to mock implementation
            return {
                "success": False,
                "error": "MAPS_API_KEY not configured",
                "address": address,
                "note": "Configure MAPS_API_KEY for real geocoding.",
            }
        
        try:
            geocode_result = self.gmaps.geocode(address)
            
            if not geocode_result:
                return {
                    "success": False,
                    "error": "No results found for the given address",
                    "address": address,
                }
            
            result = geocode_result[0]
            location = result['geometry']['location']
            
            return {
                "success": True,
                "address": address,
                "location": {
                    "latitude": location['lat'],
                    "longitude": location['lng'],
                },
                "formatted_address": result['formatted_address'],
                "place_id": result['place_id'],
                "types": result.get('types', []),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "address": address,
            }

    def _reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Reverse geocode coordinates to an address."""
        if not self.gmaps:
            return {
                "success": False,
                "error": "MAPS_API_KEY not configured",
                "location": {"latitude": latitude, "longitude": longitude},
                "note": "Configure MAPS_API_KEY for real reverse geocoding.",
            }
        
        try:
            reverse_geocode_result = self.gmaps.reverse_geocode((latitude, longitude))
            
            if not reverse_geocode_result:
                return {
                    "success": False,
                    "error": "No results found for the given coordinates",
                    "location": {"latitude": latitude, "longitude": longitude},
                }
            
            result = reverse_geocode_result[0]
            
            return {
                "success": True,
                "location": {"latitude": latitude, "longitude": longitude},
                "formatted_address": result['formatted_address'],
                "place_id": result['place_id'],
                "types": result.get('types', []),
                "address_components": result.get('address_components', []),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "location": {"latitude": latitude, "longitude": longitude},
            }

    def _get_directions(
        self, origin: str, destination: str, mode: str = "driving"
    ) -> Dict[str, Any]:
        """Get directions between two locations."""
        if not self.gmaps:
            return {
                "success": False,
                "error": "MAPS_API_KEY not configured",
                "origin": origin,
                "destination": destination,
                "note": "Configure MAPS_API_KEY for real directions.",
            }
        
        try:
            now = datetime.now()
            directions_result = self.gmaps.directions(
                origin,
                destination,
                mode=mode,
                departure_time=now
            )
            print(directions_result)
            if not directions_result:
                return {
                    "success": False,
                    "error": "No routes found",
                    "origin": origin,
                    "destination": destination,
                }
            
            routes = []
            for route in directions_result:
                leg = route['legs'][0]
                
                steps = []
                for step in leg['steps']:
                    steps.append({
                        "instruction": step['html_instructions'].replace('<b>', '').replace('</b>', '').replace('<div style="font-size:0.9em">', ' ').replace('</div>', ''),
                        "distance": step['distance']['text'],
                        "duration": step['duration']['text'],
                        "travel_mode": step['travel_mode'],
                    })
                
                routes.append({
                    "summary": route.get('summary', 'Route'),
                    "distance": {
                        "text": leg['distance']['text'],
                        "value": leg['distance']['value'],
                    },
                    "duration": {
                        "text": leg['duration']['text'],
                        "value": leg['duration']['value'],
                    },
                    "start_address": leg['start_address'],
                    "end_address": leg['end_address'],
                    "steps": steps,
                })
            
            return {
                "success": True,
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "routes": routes,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "origin": origin,
                "destination": destination,
            }

    def _calculate_distance(
        self, origins: List[str], destinations: List[str], mode: str = "driving"
    ) -> Dict[str, Any]:
        """Calculate distance matrix between locations."""
        if not self.gmaps:
            return {
                "success": False,
                "error": "MAPS_API_KEY not configured",
                "origins": origins,
                "destinations": destinations,
                "note": "Configure MAPS_API_KEY for real distance calculations.",
            }
        
        try:
            distance_result = self.gmaps.distance_matrix(
                origins,
                destinations,
                mode=mode,
                units="metric"
            )
            
            if distance_result['status'] != 'OK':
                return {
                    "success": False,
                    "error": f"API returned status: {distance_result['status']}",
                    "origins": origins,
                    "destinations": destinations,
                }
            
            matrix = []
            for i, origin in enumerate(origins):
                row = []
                for j, destination in enumerate(destinations):
                    element = distance_result['rows'][i]['elements'][j]
                    
                    if element['status'] == 'OK':
                        row.append({
                            "origin": distance_result['origin_addresses'][i],
                            "destination": distance_result['destination_addresses'][j],
                            "distance": {
                                "text": element['distance']['text'],
                                "value": element['distance']['value'],
                            },
                            "duration": {
                                "text": element['duration']['text'],
                                "value": element['duration']['value'],
                            },
                            "status": "OK",
                        })
                    else:
                        row.append({
                            "origin": origin,
                            "destination": destination,
                            "status": element['status'],
                            "error": "Route not found",
                        })
                
                matrix.append(row)
            
            return {
                "success": True,
                "origins": distance_result['origin_addresses'],
                "destinations": distance_result['destination_addresses'],
                "mode": mode,
                "matrix": matrix,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "origins": origins,
                "destinations": destinations,
            }

    def _find_nearby_places(
        self, location: str, place_type: str = None, radius: int = 1000
    ) -> Dict[str, Any]:
        """Find nearby places."""
        if not self.gmaps:
            return {
                "success": False,
                "error": "MAPS_API_KEY not configured",
                "location": location,
                "note": "Configure MAPS_API_KEY for real nearby search.",
            }
        
        try:
            # First geocode the location if it's an address
            geocode_result = self.gmaps.geocode(location)
            if not geocode_result:
                return {
                    "success": False,
                    "error": "Could not geocode location",
                    "location": location,
                }
            
            coords = geocode_result[0]['geometry']['location']
            location_coords = (coords['lat'], coords['lng'])
            
            # Search for nearby places
            places_result = self.gmaps.places_nearby(
                location=location_coords,
                radius=radius,
                type=place_type
            )
            
            if places_result['status'] not in ['OK', 'ZERO_RESULTS']:
                return {
                    "success": False,
                    "error": f"API returned status: {places_result['status']}",
                    "location": location,
                }
            
            places = []
            for place in places_result.get('results', []):
                places.append({
                    "name": place['name'],
                    "address": place.get('vicinity', 'N/A'),
                    "rating": place.get('rating'),
                    "user_ratings_total": place.get('user_ratings_total'),
                    "types": place.get('types', []),
                    "place_id": place['place_id'],
                    "location": {
                        "latitude": place['geometry']['location']['lat'],
                        "longitude": place['geometry']['location']['lng'],
                    },
                    "open_now": place.get('opening_hours', {}).get('open_now'),
                })
            
            return {
                "success": True,
                "location": location,
                "coordinates": location_coords,
                "place_type": place_type,
                "radius": radius,
                "places": places,
                "count": len(places),
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "location": location,
            }

    def _generate_static_map(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a static map URL."""
        center = params["center"]
        zoom = params.get("zoom", 13)
        size = params.get("size", "600x400")
        markers = params.get("markers", [])

        # Build Google Static Maps API URL
        base_url = "https://maps.googleapis.com/maps/api/staticmap"
        
        # URL encode center
        import urllib.parse
        center_encoded = urllib.parse.quote(center)
        
        url = f"{base_url}?center={center_encoded}&zoom={zoom}&size={size}"

        # Add markers
        if markers:
            for marker in markers:
                marker_encoded = urllib.parse.quote(marker)
                url += f"&markers={marker_encoded}"

        # Add API key if available
        if self.api_key:
            url += f"&key={self.api_key}"
        else:
            return {
                "success": False,
                "error": "MAPS_API_KEY not configured for static maps",
                "center": center,
            }

        return {
            "success": True,
            "url": url,
            "center": center,
            "zoom": zoom,
            "size": size,
            "markers": markers,
        }
