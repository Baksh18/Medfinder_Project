dependencies:2.4
flutter:3.4
sdk: flutter
google_maps_flutter: 2.1
geolocator: 8.0
http:0.13
flutter_dotenv:5.0
------------------------------------------------------------
------------------------------------------------------------
import 'package:geolocator/geolocator.dart': # type: ignore

class LocationService {
  // Get current location
  Future<Position> getCurrentLocation() async {
    bool serviceEnabled;
    LocationPermission permission;

    // Check if location services are enabled
    serviceEnabled = await Geolocator.isLocationServiceEnabled();
    if (!serviceEnabled) {
      return Future.error('Location services are disabled.');
    }

    // Check if location permissions are granted
    permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
      if (permission != LocationPermission.whileInUse && permission != LocationPermission.always) {
        return Future.error('Location permissions are denied');
      }
    }

    // Fetch and return the current position
    return await Geolocator.getCurrentPosition(desiredAccuracy: LocationAccuracy.high);
  }
}
--------------------------------------------------------------------------------------------------------------------------
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter_dotenv/flutter_dotenv.dart';

class GooglePlacesAPI {
  final String apiKey = dotenv.env['GOOGLE_API_KEY']!;

  Future<List<Map<String, dynamic>>> getHospitalsNearby(double lat, double lng) async {
    final String url =
        'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=$lat,$lng&radius=5000&type=hospital&key=$apiKey';

    final response = await http.get(Uri.parse(url));

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return List<Map<String, dynamic>>.from(data['results']);
    } else {
      throw Exception('Failed to load hospitals');
    }
  }
}
--------------------------------------------------------------------------------------------------------------------------
GOOGLE_API_KEY=your_google_api_key_here
--------------------------------------------------------------------------------------------------------------------------
import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'location_service.dart';
import 'google_places_api.dart';

class HospitalFinderScreen extends StatefulWidget {
  @override
  _HospitalFinderScreenState createState() => _HospitalFinderScreenState();
}

class _HospitalFinderScreenState extends State<HospitalFinderScreen> {
  late GoogleMapController _mapController;
  late LocationService _locationService;
  late GooglePlacesAPI _googlePlacesAPI;
  Set<Marker> _markers = Set();

  @override
  void initState() {
    super.initState();
    _locationService = LocationService();
    _googlePlacesAPI = GooglePlacesAPI();
    _loadHospitals();
  }

  // Fetch the hospitals and add markers to the map
  Future<void> _loadHospitals() async {
    try {
      Position position = await _locationService.getCurrentLocation();
      List<Map<String, dynamic>> hospitals = await _googlePlacesAPI.getHospitalsNearby(position.latitude, position.longitude);

      setState(() {
        _markers.clear();
        for (var hospital in hospitals) {
          _markers.add(Marker(
            markerId: MarkerId(hospital['place_id']),
            position: LatLng(hospital['geometry']['location']['lat'], hospital['geometry']['location']['lng']),
            infoWindow: InfoWindow(
              title: hospital['name'],
              snippet: hospital['vicinity'],
            ),
          ));
        }
      });

      _mapController.animateCamera(CameraUpdate.newLatLng(LatLng(position.latitude, position.longitude)));
    } catch (e) {
      print(e);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Hospital Finder'),
      ),
      body: GoogleMap(
        initialCameraPosition: CameraPosition(target: LatLng(37.7749, -122.4194), zoom: 12),
        markers: _markers,
        onMapCreated: (controller) {
          _mapController = controller;
        },
      ),
    );
  }
}
--------------------------------------------------------------------------------------------------------------------------
import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'hospital_finder_screen.dart';

void main() async {
  await dotenv.load(); // Load environment variables
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Hospital Finder',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: HospitalFinderScreen(),
    );
  }
}
--------------------------------------------------------------------------------------------------------------------------
