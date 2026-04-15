import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:finger/config.dart';

class ViewImages extends StatefulWidget {
  const ViewImages({super.key});

  @override
  _ViewImagesState createState() => _ViewImagesState();
}

class _ViewImagesState extends State<ViewImages> {
  List<PersonDirectory> personDirectories = [];
  bool isLoading = true;
  String get serverUrl => AppConfig.serverUrl; // Use the config
  bool _isDeleting = false;

  @override
  void initState() {
    super.initState();
    fetchDatabaseImages();
  }

  // Fetch database images from Django API
  Future<void> fetchDatabaseImages() async {
    setState(() {
      isLoading = true;
    });
    
    final url = Uri.parse('${AppConfig.baseApiUrl}/get-database-images/');
    
    try {
      final response = await http.get(url).timeout(
        const Duration(seconds: 10),
        onTimeout: () {
          throw TimeoutException('Connection timed out');
        },
      );

      if (response.statusCode == 200) {
        final Map<String, dynamic> jsonData = json.decode(response.body);
        
        // Handle empty response or error message
        if (jsonData.isEmpty) {
          setState(() {
            personDirectories = [];
            isLoading = false;
          });
          showErrorSnackbar('No registered users found in the database');
          return;
        }
        
        // Check if the response contains an error or message key
        if (jsonData.containsKey('error')) {
          showErrorSnackbar('Error: ${jsonData['error']}');
          setState(() {
            isLoading = false;
          });
          return;
        }
        
        if (jsonData.containsKey('message')) {
          showErrorSnackbar(jsonData['message']);
          setState(() {
            personDirectories = [];
            isLoading = false;
          });
          return;
        }
        
        List<PersonDirectory> tempList = [];
        
        jsonData.forEach((personId, fingerprints) {
          List<FingerprintImage> fpImages = [];
          
          (fingerprints as Map<String, dynamic>).forEach((fingerName, imagePath) {
            fpImages.add(FingerprintImage(
              fingerName: fingerName,
              imageUrl: 'https://$serverUrl$imagePath',
            ));
          });
          
          tempList.add(PersonDirectory(
            personId: personId,
            fingerprints: fpImages,
          ));
        });
        
        setState(() {
          personDirectories = tempList;
          isLoading = false;
        });
      } else {
        print('Failed to fetch data. Status code: ${response.statusCode}');
        showErrorSnackbar('Failed to fetch images (Status: ${response.statusCode})');
        setState(() {
          isLoading = false;
        });
      }
    } catch (e) {
      print('Error: $e');
      showErrorSnackbar('Connection error: ${e.toString().split(':').first}');
      setState(() {
        isLoading = false;
      });
    }
  }


  // Delete person directory
  Future<void> _deletePersonDirectory(String personId) async {
    // Prevent multiple delete operations
    if (_isDeleting) return;
    
    setState(() {
      _isDeleting = true;
    });
    
    try {
      // Remove from local list first for immediate UI feedback
      setState(() {
        personDirectories.removeWhere((dir) => dir.personId == personId);
      });
      
      // Show a "deleting" indicator
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Row(
              children: [
                const SizedBox(
                  width: 20, 
                  height: 20, 
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                  ),
                ),
                const SizedBox(width: 16),
                Text('Deleting Person ID: $personId...'),
              ],
            ),
            duration: const Duration(seconds: 30), // Long duration as we'll dismiss it manually
          ),
        );
      }
      
      // Send delete request to server
      final url = Uri.parse('${AppConfig.baseApiUrl}/delete-person/');
      
      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
        },
        body: json.encode({'person_id': personId}),
      ).timeout(const Duration(seconds: 15));
      
      // Dismiss the "deleting" snackbar
      if (mounted) {
        ScaffoldMessenger.of(context).hideCurrentSnackBar();
      }
      
      if (response.statusCode == 200) {
        // Show success message
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Person ID: $personId deleted successfully'),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 3),
            ),
          );
        }
      } else {
        // Show error message
        final Map<String, dynamic> responseData = json.decode(response.body);
        final errorMessage = responseData['error'] ?? 'Failed to delete person';
        
        throw Exception(errorMessage);
      }
    } catch (e) {
      print('Error deleting person: $e');
      
      // Add the person back to the list if deletion failed
      await fetchDatabaseImages();
      
      showErrorSnackbar('Error deleting person: ${e.toString().split(':').last.trim()}');
    } finally {
      setState(() {
        _isDeleting = false;
      });
    }
  }
  
  // Fetch CSRF token
  Future<String?> _fetchCsrfToken() async {
    try {
      final response = await http.get(
        Uri.parse('${AppConfig.baseApiUrl}/get-csrf-token/'),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
      ).timeout(const Duration(seconds: 5));
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['csrfToken'];
      }
      print('Failed to fetch CSRF token. Status: ${response.statusCode}');
      return null;
    } catch (e) {
      print('Error fetching CSRF token: $e');
      return null;
    }
  }

  void showErrorSnackbar(String message) {
    if (!mounted) return;
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        action: SnackBarAction(
          label: 'Retry',
          onPressed: fetchDatabaseImages,
          textColor: Colors.white,
        ),
        duration: const Duration(seconds: 5),
      ),
    );
  }

  // Show full-screen image
  void showFullScreenImage(String imageUrl, String fingerName) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (context) => FullScreenImageView(
          imageUrl: imageUrl,
          fingerName: fingerName,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Database Images',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 22),
        ),
        backgroundColor: const Color(0xFF0F172A),
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: fetchDatabaseImages,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0F172A), Color(0xFF1E293B)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: isLoading
            ? const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(
                      valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF3B82F6)),
                    ),
                    SizedBox(height: 16),
                    Text(
                      'Loading database images...',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
              )
            : personDirectories.isEmpty
                ? Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Icon(
                          Icons.folder_off,
                          size: 70,
                          color: Colors.white30,
                        ),
                        const SizedBox(height: 16),
                        const Text(
                          'No registered users found',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w600,
                            color: Colors.white70,
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Register new users to see their fingerprints here',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.white38,
                          ),
                          textAlign: TextAlign.center,
                        ),
                        const SizedBox(height: 24),
                        ElevatedButton.icon(
                          icon: const Icon(Icons.refresh),
                          label: const Text('Refresh'),
                          onPressed: fetchDatabaseImages,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF3B82F6),
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 24,
                              vertical: 12,
                            ),
                          ),
                        ),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: personDirectories.length,
                    itemBuilder: (context, index) {
                      final personDir = personDirectories[index];
                      
                      return Dismissible(
                        key: Key(personDir.personId),
                        direction: DismissDirection.endToStart,
                        background: Container(
                          alignment: Alignment.centerRight,
                          padding: const EdgeInsets.only(right: 20.0),
                          decoration: BoxDecoration(
                            color: Colors.red,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.delete_forever,
                                color: Colors.white,
                                size: 36,
                              ),
                              SizedBox(height: 4),
                              Text(
                                'Delete',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ],
                          ),
                        ),
                        confirmDismiss: (direction) async {
                          return await showDialog(
                            context: context,
                            builder: (BuildContext context) {
                              return AlertDialog(
                                title: const Text("Confirm Deletion"),
                                content: Text(
                                  "Are you sure you want to delete Person ID: ${personDir.personId} and all associated fingerprints?",
                                ),
                                actions: <Widget>[
                                  TextButton(
                                    onPressed: () => Navigator.of(context).pop(false),
                                    child: const Text("CANCEL"),
                                  ),
                                  TextButton(
                                    onPressed: () => Navigator.of(context).pop(true),
                                    child: const Text(
                                      "DELETE",
                                      style: TextStyle(color: Colors.red),
                                    ),
                                  ),
                                ],
                              );
                            },
                          );
                        },
                        onDismissed: (direction) {
                          _deletePersonDirectory(personDir.personId);
                        },
                        child: Card(
                          margin: const EdgeInsets.only(bottom: 16),
                          color: const Color(0xFF1E293B),
                          elevation: 4,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: ExpansionTile(
                            initiallyExpanded: false,
                            collapsedBackgroundColor: const Color(0xFF1E293B),
                            backgroundColor: const Color(0xFF1E293B),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            collapsedShape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            title: Text(
                              'Person ID: ${personDir.personId}',
                              style: const TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                            subtitle: Text(
                              '${personDir.fingerprints.length} fingerprint images',
                              style: const TextStyle(
                                fontSize: 14,
                                color: Colors.white60,
                              ),
                            ),
                            children: [
                              GridView.builder(
                                shrinkWrap: true,
                                physics: const NeverScrollableScrollPhysics(),
                                padding: const EdgeInsets.all(12),
                                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                                  crossAxisCount: 2,
                                  crossAxisSpacing: 12,
                                  mainAxisSpacing: 12,
                                  childAspectRatio: 0.8,
                                ),
                                itemCount: personDir.fingerprints.length,
                                itemBuilder: (context, fpIndex) {
                                  final fingerprint = personDir.fingerprints[fpIndex];
                                  return GestureDetector(
                                    onTap: () => showFullScreenImage(
                                      fingerprint.imageUrl,
                                      fingerprint.fingerName,
                                    ),
                                    child: Container(
                                      decoration: BoxDecoration(
                                        color: const Color(0xFF0F172A),
                                        borderRadius: BorderRadius.circular(10),
                                        border: Border.all(
                                          color: const Color(0xFF3B82F6).withOpacity(0.3),
                                          width: 1,
                                        ),
                                      ),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.stretch,
                                        children: [
                                          Expanded(
                                            child: ClipRRect(
                                              borderRadius: const BorderRadius.vertical(
                                                top: Radius.circular(9),
                                              ),
                                              child: Image.network(
                                                fingerprint.imageUrl,
                                                fit: BoxFit.cover,
                                                loadingBuilder: (context, child, loadingProgress) {
                                                  if (loadingProgress == null) return child;
                                                  return Center(
                                                    child: CircularProgressIndicator(
                                                      value: loadingProgress.expectedTotalBytes != null
                                                          ? loadingProgress.cumulativeBytesLoaded /
                                                              (loadingProgress.expectedTotalBytes ?? 1)
                                                          : null,
                                                      valueColor: const AlwaysStoppedAnimation<Color>(
                                                        Color(0xFF3B82F6),
                                                      ),
                                                    ),
                                                  );
                                                },
                                                errorBuilder: (context, error, stackTrace) {
                                                  return const Center(
                                                    child: Icon(
                                                      Icons.broken_image,
                                                      size: 40,
                                                      color: Colors.white30,
                                                    ),
                                                  );
                                                },
                                              ),
                                            ),
                                          ),
                                          Padding(
                                            padding: const EdgeInsets.all(8.0),
                                            child: Text(
                                              _formatFingerName(fingerprint.fingerName),
                                              style: const TextStyle(
                                                color: Colors.white,
                                                fontWeight: FontWeight.w500,
                                                fontSize: 14,
                                              ),
                                              textAlign: TextAlign.center,
                                            ),
                                          ),
                                        ],
                                      ),
                                    ),
                                  );
                                },
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
      ),
    );
  }
  
  // Helper method to format finger names
  String _formatFingerName(String name) {
    // Convert 'left_thumb' to 'Left Thumb'
    List<String> parts = name.split('_');
    for (int i = 0; i < parts.length; i++) {
      if (parts[i].isNotEmpty) {
        parts[i] = parts[i][0].toUpperCase() + parts[i].substring(1);
      }
    }
    return parts.join(' ');
  }
}

// Models
class PersonDirectory {
  final String personId;
  final List<FingerprintImage> fingerprints;

  PersonDirectory({
    required this.personId,
    required this.fingerprints,
  });
}

class FingerprintImage {
  final String fingerName;
  final String imageUrl;

  FingerprintImage({
    required this.fingerName,
    required this.imageUrl,
  });
}

// Full-Screen Image View
class FullScreenImageView extends StatelessWidget {
  final String imageUrl;
  final String fingerName;

  const FullScreenImageView({
    super.key, 
    required this.imageUrl,
    required this.fingerName,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        iconTheme: const IconThemeData(color: Colors.white),
        title: Text(
          _formatFingerName(fingerName),
          style: const TextStyle(color: Colors.white),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.download),
            onPressed: () {
              // TODO: Implement download functionality
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Download feature coming soon'),
                ),
              );
            },
            tooltip: 'Download image',
          ),
        ],
      ),
      body: InteractiveViewer(
        minScale: 0.5,
        maxScale: 4.0,
        child: Center(
          child: Image.network(
            imageUrl,
            fit: BoxFit.contain,
            loadingBuilder: (context, child, loadingProgress) {
              if (loadingProgress == null) return child;
              return Center(
                child: CircularProgressIndicator(
                  value: loadingProgress.expectedTotalBytes != null
                      ? loadingProgress.cumulativeBytesLoaded /
                          (loadingProgress.expectedTotalBytes ?? 1)
                      : null,
                  valueColor: const AlwaysStoppedAnimation<Color>(
                    Colors.white70,
                  ),
                ),
              );
            },
            errorBuilder: (context, error, stackTrace) {
              return Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(
                    Icons.broken_image,
                    size: 80,
                    color: Colors.grey,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Failed to load image: ${error.toString().split(':').first}',
                    style: const TextStyle(color: Colors.grey),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 24),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.refresh),
                    label: const Text('Retry'),
                    onPressed: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => FullScreenImageView(
                            imageUrl: imageUrl,
                            fingerName: fingerName,
                          ),
                        ),
                      );
                    },
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }
  
  // Helper method to format finger names
  String _formatFingerName(String name) {
    // Convert 'left_thumb' to 'Left Thumb'
    List<String> parts = name.split('_');
    for (int i = 0; i < parts.length; i++) {
      if (parts[i].isNotEmpty) {
        parts[i] = parts[i][0].toUpperCase() + parts[i].substring(1);
      }
    }
    return parts.join(' ');
  }
}

class TimeoutException implements Exception {
  final String message;
  TimeoutException(this.message);
  
  @override
  String toString() => message;
}
