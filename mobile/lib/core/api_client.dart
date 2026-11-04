import 'package:dio/dio.dart';
import 'config.dart';

class TokenStore {
  String? accessToken;
  String? refreshToken;
  void clear() {
    accessToken = null;
    refreshToken = null;
  }
}

class ApiClient {
  ApiClient(this.tokens) {
    dio = Dio(BaseOptions(
      baseUrl: AppConfig.apiBaseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 20),
      headers: {'Accept': 'application/json'},
    ));
    dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) {
        if (tokens.accessToken != null) {
          options.headers['Authorization'] = 'Bearer ${tokens.accessToken}';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401 &&
            tokens.refreshToken != null &&
            !error.requestOptions.path.endsWith('/auth/refresh')) {
          try {
            final response = await dio.post('/auth/refresh',
                data: {'refresh_token': tokens.refreshToken});
            tokens.accessToken = response.data['access_token'] as String;
            tokens.refreshToken = response.data['refresh_token'] as String;
            final request = error.requestOptions;
            request.headers['Authorization'] = 'Bearer ${tokens.accessToken}';
            handler.resolve(await dio.fetch(request));
            return;
          } catch (_) {
            tokens.clear();
          }
        }
        handler.next(error);
      },
    ));
  }

  late final Dio dio;
  final TokenStore tokens;
}
