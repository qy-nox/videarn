import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/user.dart';

class AuthRepository {
  AuthRepository(this.client);
  final ApiClient client;

  Future<AppUser> currentUser() async {
    final response = await client.dio.get('/auth/me');
    return AppUser.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> firebaseLogin(String idToken) async {
    final response = await client.dio.post('/auth/firebase-login',
        data: {'id_token': idToken});
    client.tokens.accessToken = response.data['access_token'] as String;
    client.tokens.refreshToken = response.data['refresh_token'] as String;
  }

  Future<void> logout() async {
    try {
      await client.dio.post('/auth/logout');
    } on DioException {
      // Local logout must still complete if the network is unavailable.
    } finally {
      client.tokens.clear();
    }
  }
}
