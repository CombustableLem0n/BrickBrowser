import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:typed_data';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

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
  Uint8List? _selectedImageBytes; // To hold image in bytes
  Uint8List? _alteredImageBytes; // To hold altered image bytes
  String? _selectedImagePath; // Store the image path for `fromPath`
  final String _defaultImagePath = "assets/sillydog1.jpg"; // Default asset image

  // Pick an image using image_picker
  Future<void> _pickImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);

    if (image != null) {
      Uint8List imageBytes = await image.readAsBytes();
      setState(() {
        _selectedImageBytes = imageBytes; // Store the selected image bytes
        _selectedImagePath = image.path; // Store the file path
      });
    }
  }

  // Upload selected image to the Flask server and get the altered version
  Future<void> _uploadImage() async {
  if (_selectedImageBytes == null) {
    print("No image selected.");
    return;
  }

  var uri = Uri.parse('http://127.0.0.1:5000/image');
  var request = http.MultipartRequest('POST', uri);

  // Create a multipart file from bytes with a filename
  var pic = http.MultipartFile.fromBytes(
    'image', 
    _selectedImageBytes!,
    filename: 'upload.jpg', // Add a filename for compatibility
  );

  request.files.add(pic);
  request.headers.addAll({
    "Content-Type": "multipart/form-data",
  });

  try {
    var response = await request.send();

    if (response.statusCode == 200) {
      var responseBytes = await response.stream.toBytes();
      setState(() {
        _alteredImageBytes = responseBytes; // Set the altered image bytes
      });
      print("Image uploaded successfully!");
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        title: Text(widget.title),
      ),
      body: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Display either selected image or default image
          _selectedImageBytes == null
              ? Image.asset(_defaultImagePath) // Show default image
              : Image.memory(_selectedImageBytes!), // Show picked image

          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: _pickImage,
            child: const Text("Pick an Image"),
          ),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: _uploadImage,
            child: const Text("Upload Image"),
          ),
          const SizedBox(height: 20),
          // Display the altered image
          if (_alteredImageBytes != null)
            Image.memory(_alteredImageBytes!), // Show the altered image
        ],
      ),
    );
  }
}
