import 'dart:convert';
import 'dart:typed_data';
import 'dart:math';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:http/http.dart' as http;
import 'package:crypto/crypto.dart'; // Added for BrickLink OAuth

// Add url_launcher import
import 'package:url_launcher/url_launcher.dart';

// Rename the helper function to avoid conflict with launchUrl from the package
Future<void> openUrl(Uri url) async {
  if (!await launchUrl(url)) {
    throw Exception('Could not launch $url');
  }
}

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Demo',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      home: const MyHomePage(title: 'Pick & Upload Image'),
    );
  }
}

class MyHomePage extends StatefulWidget {
  const MyHomePage({super.key, required this.title});
  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}

class _MyHomePageState extends State<MyHomePage> {
  Uint8List? _selectedImageBytes;
  List<Uint8List> _resultImages = [];
  List<String> _resultLabels = [];
  int _currentIndex = 0;
  final String _defaultImagePath = "assets/sillydog1.jpg";

  final Map<int, String> labelToPart = {
    1: '32505',
    2: '32565',
    // Add more mappings as needed
  };

  Future<void> _pickImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);

    if (image != null) {
      Uint8List imageBytes = await image.readAsBytes();
      setState(() {
        _selectedImageBytes = imageBytes;
        _resultImages = [];
        _resultLabels = [];
        _currentIndex = 0;
      });
      print("Image picked, bytes length: ${imageBytes.length}");
    } else {
      print("No image selected.");
    }
  }

  Future<void> _uploadImage() async {
    if (_selectedImageBytes == null) {
      print("No image selected.");
      return;
    }

    String? fileExtension;
    if (_selectedImageBytes!.sublist(0, 2).toString() == '[137, 80]') {
      fileExtension = 'png';
    } else if (_selectedImageBytes!.sublist(0, 3).toString() == '[255, 216, 255]') {
      fileExtension = 'jpg';
    } else {
      fileExtension = 'jpg';
    }

    var uri = Uri.parse('http://127.0.0.1:5000/image');
    var request = http.MultipartRequest('POST', uri);

    String filename = 'upload.$fileExtension';

    var pic = http.MultipartFile.fromBytes(
      'image',
      _selectedImageBytes!,
      filename: filename,
    );

    request.files.add(pic);
    request.headers.addAll({
      "Content-Type": "multipart/form-data",
    });

    try {
      var response = await request.send();

      print("Upload request sent. Status code: ${response.statusCode}");

      if (response.statusCode == 200) {
        var responseString = await response.stream.bytesToString();
        print("Upload response string: $responseString");

        var jsonResponse = json.decode(responseString);

        List<dynamic> results = jsonResponse['results'];

        List<Uint8List> images = [];
        List<String> labels = [];

        for (var result in results) {
          String base64Img = result['image_base64'];
          int label = result['label'];

          images.add(base64Decode(base64Img));
          labels.add(labelToPart[label] ?? "Unknown Part");
        }

        setState(() {
          _resultImages = images;
          _resultLabels = labels;
          _currentIndex = 0;
        });

        print("Images received: ${images.length}");
      } else {
        print('Failed to upload image: ${response.statusCode}');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to upload image, error: ${response.statusCode}')),
        );
      }
    } catch (e) {
      print('Error uploading image: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error uploading image: $e')),
      );
    }
  }

  List<Map<String, dynamic>> _sets = [];

  // NEW function to fetch images for parts
  Future<void> fetchPartImages(List<String> partNumbers) async {
    final url = Uri.parse('http://127.0.0.1:5000/part-images');

    try {
      final response = await http.post(
        url,
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({'part_numbers': partNumbers}),
      );

      print("fetchPartImages: Status code: ${response.statusCode}");
      print("fetchPartImages: Response body: ${response.body}");

      if (response.statusCode == 200) {
        final jsonResponse = jsonDecode(response.body);

        if (jsonResponse['images'] != null && jsonResponse['images'] is List) {
          setState(() {
            _sets = List<Map<String, dynamic>>.from(jsonResponse['images']);
          });
          print('fetchPartImages: Images loaded: $_sets');
        } else {
          print("fetchPartImages: 'images' key missing or not a List");
        }
      } else {
        print("fetchPartImages: Error status code: ${response.statusCode}");
      }
    } catch (e) {
      print("fetchPartImages: Exception caught: $e");
    }
  }

  void _showPreviousImage() {
    setState(() {
      if (_currentIndex > 0) _currentIndex--;
    });
  }

  void _showNextImage() {
    setState(() {
      if (_currentIndex < _resultImages.length - 1) _currentIndex++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: SingleChildScrollView(
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                _selectedImageBytes == null
                    ? Image.asset(_defaultImagePath, height: 300, fit: BoxFit.contain)
                    : Image.memory(_selectedImageBytes!, height: 300, fit: BoxFit.contain),
                const SizedBox(height: 20),
                ElevatedButton(onPressed: _pickImage, child: const Text("Pick an Image")),
                const SizedBox(height: 20),
                ElevatedButton(onPressed: _uploadImage, child: const Text("Upload Image")),
                const SizedBox(height: 20),
                if (_sets.isNotEmpty)
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text("BrickLink Part Images:", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                      ..._sets.map((set) => ListTile(
                            leading: set['image_url'] != null
                                ? Image.network(set['image_url'], width: 50)
                                : const Icon(Icons.image_not_supported),
                            title: Text(set['part_number'] ?? "Unknown Part"),
                            subtitle: Text("ID: ${set['part_number'] ?? "N/A"}"),
                            onTap: () {
                              final url = Uri.parse(set['external_url']);
                              openUrl(url);
                            },
                          )),
                    ],
                  ),
                ElevatedButton(
                  onPressed: () {
                    // Extract unique part numbers from _resultLabels, ignoring unknowns
                    List<String> partsToFetch = _resultLabels
                        .where((label) => label != "Unknown Part")
                        .toSet()
                        .toList();

                    if (partsToFetch.isEmpty) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text("No valid parts detected to fetch.")),
                      );
                      return;
                    }

                    fetchPartImages(partsToFetch);
                  },
                  child: const Text("Get BrickLink Images for Detected Parts"),
                ),
                const SizedBox(height: 20),
                if (_resultImages.isNotEmpty)
                  Column(
                    children: [
                      Text(
                        "Part: ${_resultLabels[_currentIndex]}",
                        style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 10),
                      Image.memory(
                        _resultImages[_currentIndex],
                        height: 300,
                        fit: BoxFit.contain,
                      ),
                      const SizedBox(height: 10),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          ElevatedButton(
                            onPressed: _currentIndex > 0 ? _showPreviousImage : null,
                            child: const Icon(Icons.arrow_left),
                          ),
                          const SizedBox(width: 20),
                          ElevatedButton(
                            onPressed: _currentIndex < _resultImages.length - 1 ? _showNextImage : null,
                            child: const Icon(Icons.arrow_right),
                          ),
                        ],
                      ),
                    ],
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
