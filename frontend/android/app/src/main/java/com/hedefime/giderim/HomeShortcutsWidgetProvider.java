package com.hedefime.giderim;

import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.widget.RemoteViews;

/**
 * Akilli kisayol widget'i (2x2): tek tikla "Eve Git" / "Ise Git".
 * Butonlar uygulamayi hng://go derin baglantisiyla acar; JS tarafi
 * (App.tsx appUrlOpen dinleyicisi) sabit konumu okuyup rotayi baslatir.
 */
public class HomeShortcutsWidgetProvider extends AppWidgetProvider {

    private static PendingIntent goIntent(Context context, String target, int code) {
        Uri uri = Uri.parse("hng://go?target=" + target);
        Intent intent = new Intent(Intent.ACTION_VIEW, uri);
        intent.setClass(context, MainActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        return PendingIntent.getActivity(
                context, code, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    @Override
    public void onUpdate(Context context, AppWidgetManager manager, int[] appWidgetIds) {
        for (int id : appWidgetIds) {
            RemoteViews rv = new RemoteViews(
                    context.getPackageName(), R.layout.widget_home_shortcuts);
            rv.setOnClickPendingIntent(R.id.widget_go_home, goIntent(context, "home", 101));
            rv.setOnClickPendingIntent(R.id.widget_go_work, goIntent(context, "work", 102));
            manager.updateAppWidget(id, rv);
        }
    }
}
