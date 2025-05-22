import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

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
  Uint8List? _alteredImageBytes;
  String? _selectedImagePath;
  final String _defaultImagePath = "assets/sillydog1.jpg";

  Future<void> _pickImage() async {
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);

    if (image != null) {
      Uint8List imageBytes = await image.readAsBytes();
      setState(() {
        _selectedImageBytes = imageBytes;
        _selectedImagePath = image.path;
      });
    }
  }

      Future<void> _uploadImage() async {
    if (_selectedImageBytes == null) {
      print("No image selected.");
      return;
    }

    // Determine the file extension by checking the first few bytes of the image
    String? fileExtension;
    if (_selectedImageBytes!.sublist(0, 2).toString() == '[137, 80]') {
      fileExtension = 'png';  // PNG images start with 137 80
    } else if (_selectedImageBytes!.sublist(0, 3).toString() == '[255, 216, 255]') {
      fileExtension = 'jpg';  // JPG images start with FF D8 FF
    } else {
      fileExtension = 'jpg';  // Default to jpg if type is unknown
    }

    var uri = Uri.parse('http://127.0.0.1:5000/image');
    var request = http.MultipartRequest('POST', uri);

    // Create the filename with the correct extension
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

      if (response.statusCode == 200) {
        var responseBytes = await response.stream.toBytes();
        setState(() {
          _alteredImageBytes = responseBytes;
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
      body: SingleChildScrollView(  // Enables scrolling
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                _selectedImageBytes == null
                  ? Image.asset(_defaultImagePath, height: 300, fit: BoxFit.contain)
                  : Image.memory(
                      _selectedImageBytes!,
                      height: 300,
                      fit: BoxFit.contain,
                    ),

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

                if (_alteredImageBytes != null)
                  Image.memory(
                    _alteredImageBytes!,
                    height: 300,
                    fit: BoxFit.contain,
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
