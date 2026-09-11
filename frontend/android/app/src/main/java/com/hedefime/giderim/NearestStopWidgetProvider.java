package com.hedefime.giderim;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.location.Location;
import android.location.LocationManager;
import android.os.Handler;
import android.os.Looper;
import android.widget.RemoteViews;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.List;

/**
 * Ana ekran widget'i: en yakin durak + sonraki kalkislar.
 * Konum icin aktif GPS istemez; son bilinen konumu okur (izin varsa).
 * Veriyi backend /nearby-stops + /stop-departures'tan alir.
 */
public class NearestStopWidgetProvider extends AppWidgetProvider {

    private static final String API_BASE = "https://hedefime-nasil-giderim-api.onrender.com";
    public static final String ACTION_REFRESH = "com.hedefime.giderim.WIDGET_REFRESH";

    @Override
    public void onUpdate(Context context, AppWidgetManager manager, int[] appWidgetIds) {
        for (int id : appWidgetIds) {
            renderLoading(context, manager, id);
        }
        refreshAll(context);
    }

    @Override
    public void onReceive(Context context, Intent intent) {
        super.onReceive(context, intent);
        if (ACTION_REFRESH.equals(intent.getAction())) {
            AppWidgetManager manager = AppWidgetManager.getInstance(context);
            int[] ids = manager.getAppWidgetIds(
                    new ComponentName(context, NearestStopWidgetProvider.class));
            for (int id : ids) {
                renderLoading(context, manager, id);
            }
            refreshAll(context);
        }
    }

    private static void renderLoading(Context context, AppWidgetManager manager, int appWidgetId) {
        RemoteViews rv = baseViews(context);
        rv.setTextViewText(R.id.widget_stop_name, context.getString(R.string.widget_loading));
        rv.removeAllViews(R.id.widget_rows);
        manager.updateAppWidget(appWidgetId, rv);
    }

    private static RemoteViews baseViews(Context context) {
        RemoteViews rv = new RemoteViews(context.getPackageName(), R.layout.widget_nearest_stop);

        // Widget'a dokun -> uygulamayi ac
        Intent open = new Intent(context, MainActivity.class);
        PendingIntent openPi = PendingIntent.getActivity(
                context, 0, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        rv.setOnClickPendingIntent(R.id.widget_root, openPi);

        // ↻ -> yenile
        Intent refresh = new Intent(context, NearestStopWidgetProvider.class);
        refresh.setAction(ACTION_REFRESH);
        PendingIntent refreshPi = PendingIntent.getBroadcast(
                context, 1, refresh,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        rv.setOnClickPendingIntent(R.id.widget_refresh, refreshPi);

        return rv;
    }

    private static void refreshAll(Context context) {
        Thread t = new Thread(() -> {
            String error = null;
            String stopLine = null;
            String[][] deps = null;

            Location loc = lastKnownLocation(context);
            if (loc == null) {
                error = context.getString(R.string.widget_open_app);
            } else {
                try {
                    JSONObject stop = fetchNearestStop(loc.getLatitude(), loc.getLongitude());
                    if (stop != null) {
                        String city = stop.optString("city", "");
                        String name = stop.optString("name", "");
                        JSONArray lines = stop.optJSONArray("lines");
                        stopLine = name;

                        StringBuilder body = new StringBuilder("{\"city\":")
                                .append(q(city)).append(",\"stop\":").append(q(name));
                        if (stop.has("lat") && stop.has("lon")) {
                            body.append(",\"lat\":").append(stop.optDouble("lat"))
                                .append(",\"lon\":").append(stop.optDouble("lon"));
                        }
                        body.append(",\"lines\":[");
                        if (lines != null) {
                            int n = Math.min(lines.length(), 4);
                            for (int i = 0; i < n; i++) {
                                if (i > 0) body.append(",");
                                body.append(q(lines.optString(i, "")));
                            }
                        }
                        body.append("]}");

                        JSONArray arr = fetchJson(
                                API_BASE + "/stop-departures", "POST", body.toString())
                                .optJSONArray("departures");
                        if (arr != null && arr.length() > 0) {
                            int n = Math.min(arr.length(), 4);
                            deps = new String[n][];
                            for (int i = 0; i < n; i++) {
                                JSONObject d = arr.optJSONObject(i);
                                if (d == null) continue;
                                String line = d.optString("line", "");
                                int sp = line.indexOf(' ');
                                if (sp > 0) line = line.substring(0, sp);
                                String time = d.optString("time", "");
                                int mins = d.optInt("minutes_ahead", -1);
                                String ma = mins >= 0 ? " (" + mins + " dk)" : "";
                                deps[i] = new String[]{line, time + ma};
                            }
                        }
                    } else {
                        error = context.getString(R.string.widget_no_stop);
                    }
                } catch (Exception e) {
                    error = context.getString(R.string.widget_error);
                }
            }

            final String fStop = stopLine;
            final String[][] fDeps = deps;
            final String fError = error;
            new Handler(Looper.getMainLooper()).post(() -> {
                AppWidgetManager manager = AppWidgetManager.getInstance(context);
                int[] ids = manager.getAppWidgetIds(
                        new ComponentName(context, NearestStopWidgetProvider.class));
                for (int id : ids) {
                    RemoteViews rv = baseViews(context);
                    if (fError != null) {
                        rv.setTextViewText(R.id.widget_stop_name, fError);
                        rv.removeAllViews(R.id.widget_rows);
                    } else {
                        rv.setTextViewText(R.id.widget_stop_name, fStop);
                        rv.removeAllViews(R.id.widget_rows);
                        if (fDeps != null) {
                            for (String[] d : fDeps) {
                                if (d == null) continue;
                                RemoteViews row = new RemoteViews(context.getPackageName(),
                                        android.R.layout.simple_list_item_1);
                                row.setTextViewText(android.R.id.text1,
                                        d[0] + "  ·  " + d[1]);
                                row.setTextColor(android.R.id.text1, 0xFFE6EDF7);
                                rv.addView(R.id.widget_rows, row);
                            }
                        }
                    }
                    manager.updateAppWidget(id, rv);
                }
            });
        });
        t.setDaemon(true);
        t.start();
    }

    private static Location lastKnownLocation(Context context) {
        try {
            LocationManager lm = (LocationManager) context.getSystemService(Context.LOCATION_SERVICE);
            if (lm == null) return null;
            if (context.checkSelfPermission(android.Manifest.permission.ACCESS_FINE_LOCATION)
                    != android.content.pm.PackageManager.PERMISSION_GRANTED
                    && context.checkSelfPermission(android.Manifest.permission.ACCESS_COARSE_LOCATION)
                    != android.content.pm.PackageManager.PERMISSION_GRANTED) {
                return null;
            }
            Location best = null;
            List<String> providers = lm.getProviders(true);
            for (String p : providers) {
                Location l = lm.getLastKnownLocation(p);
                if (l != null && (best == null || l.getTime() > best.getTime())) {
                    best = l;
                }
            }
            return best;
        } catch (Exception e) {
            return null;
        }
    }

    private static JSONObject fetchNearestStop(double lat, double lon) throws Exception {
        String url = API_BASE + "/nearby-stops?lat=" + lat + "&lon=" + lon + "&limit=1";
        JSONArray results = fetchJson(url, "GET", null).optJSONArray("results");
        return (results != null && results.length() > 0) ? results.optJSONObject(0) : null;
    }

    private static JSONObject fetchJson(String urlStr, String method, String body) throws Exception {
        HttpURLConnection conn = (HttpURLConnection) new URL(urlStr).openConnection();
        try {
            conn.setConnectTimeout(15000);
            conn.setReadTimeout(20000);
            conn.setRequestMethod(method);
            conn.setRequestProperty("Accept", "application/json");
            if (body != null) {
                conn.setDoOutput(true);
                conn.setRequestProperty("Content-Type", "application/json");
                try (OutputStream os = conn.getOutputStream()) {
                    os.write(body.getBytes(StandardCharsets.UTF_8));
                }
            }
            int code = conn.getResponseCode();
            InputStream is = code >= 400 ? conn.getErrorStream() : conn.getInputStream();
            StringBuilder sb = new StringBuilder();
            if (is != null) {
                try (BufferedReader br = new BufferedReader(
                        new InputStreamReader(is, StandardCharsets.UTF_8))) {
                    String line;
                    while ((line = br.readLine()) != null) sb.append(line);
                }
            }
            if (code >= 400) throw new Exception("HTTP " + code);
            return new JSONObject(sb.toString());
        } finally {
            conn.disconnect();
        }
    }

    private static String q(String s) {
        return "\"" + (s == null ? "" : s.replace("\\", "\\\\").replace("\"", "\\\"")) + "\"";
    }
}
