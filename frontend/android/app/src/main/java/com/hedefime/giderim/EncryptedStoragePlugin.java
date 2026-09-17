package com.hedefime.giderim;

import android.content.ContentValues;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;

import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKey;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import net.zetetic.database.sqlcipher.SQLiteDatabase;

import java.security.SecureRandom;

/**
 * Only stores session data that must not be exposed in WebView localStorage.
 * SQLCipher encrypts the database and Android Keystore encrypts its passphrase.
 */
@CapacitorPlugin(name = "EncryptedStorage")
public class EncryptedStoragePlugin extends Plugin {
    private static final String DATABASE_NAME = "hng_secure_store.db";
    private static final String PASSPHRASE_KEY = "sqlcipher_passphrase";
    private static final String PREFS_NAME = "hng_secure_store_key";
    private static final String FALLBACK_PREFS_NAME = "hng_secure_store_key_fallback";
    private static final String TABLE = "secure_values";

    private SQLiteDatabase database;
    private String initError;

    @Override
    public void load() {
        try {
            String passphrase = getPassphrase();
            database = SQLiteDatabase.openOrCreateDatabase(
                getContext().getDatabasePath(DATABASE_NAME), passphrase, null, null
            );
            database.execSQL("CREATE TABLE IF NOT EXISTS " + TABLE
                + " (key TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL)");
        } catch (Throwable exception) {
            // Baslatma patlarsa uygulamayi dusurme: cagrilar reject edilir,
            // JS tarafi (hydrateAuthSession) yakalar ve kullanici yeniden giris yapar.
            android.util.Log.e("EncryptedStorage", "Sifreli depo baslatilamadi.", exception);
            initError = "Sifreli yerel depo kullanilamiyor.";
            database = null;
        }
    }

    private boolean isReady(PluginCall call) {
        if (database == null) {
            call.reject(initError != null ? initError : "Sifreli yerel depo hazir degil.");
            return false;
        }
        return true;
    }

    @PluginMethod
    public void get(PluginCall call) {
        if (!isReady(call)) return;
        String key = call.getString("key");
        if (!isValidKey(key, call)) return;

        String value = null;
        try (Cursor cursor = database.rawQuery(
            "SELECT value FROM " + TABLE + " WHERE key = ?", new String[]{key}
        )) {
            if (cursor.moveToFirst()) value = cursor.getString(0);
        }
        JSObject result = new JSObject();
        result.put("value", value);
        call.resolve(result);
    }

    @PluginMethod
    public void set(PluginCall call) {
        if (!isReady(call)) return;
        String key = call.getString("key");
        String value = call.getString("value");
        if (!isValidKey(key, call)) return;
        if (value == null) {
            call.reject("value gerekli.");
            return;
        }

        ContentValues values = new ContentValues();
        values.put("key", key);
        values.put("value", value);
        database.insertWithOnConflict(TABLE, null, values, SQLiteDatabase.CONFLICT_REPLACE);
        call.resolve();
    }

    @PluginMethod
    public void remove(PluginCall call) {
        if (!isReady(call)) return;
        String key = call.getString("key");
        if (!isValidKey(key, call)) return;
        database.delete(TABLE, "key = ?", new String[]{key});
        call.resolve();
    }

    private boolean isValidKey(String key, PluginCall call) {
        if (key == null || key.isEmpty() || key.length() > 128) {
            call.reject("Gecersiz anahtar.");
            return false;
        }
        return true;
    }

    private String getPassphrase() throws Exception {
        Context context = getContext();

        // 1. Oncelikle Android Keystore ile sifrelenmis tercihlerde ara.
        try {
            MasterKey masterKey = new MasterKey.Builder(context)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build();
            SharedPreferences preferences = EncryptedSharedPreferences.create(
                context,
                PREFS_NAME,
                masterKey,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            );
            String passphrase = preferences.getString(PASSPHRASE_KEY, null);
            if (passphrase != null) return passphrase;

            passphrase = generatePassphrase();
            preferences.edit().putString(PASSPHRASE_KEY, passphrase).commit();
            return passphrase;
        } catch (Throwable t) {
            android.util.Log.w("EncryptedStorage", "Keystore/EncryptedSharedPreferences basarisiz, normal tercihlere dusuluyor.", t);
        }

        // 2. Guvenlik donanimi calismazsa duz SharedPreferences'a dus.
        SharedPreferences fallback = context.getSharedPreferences(FALLBACK_PREFS_NAME, Context.MODE_PRIVATE);
        String fallbackPassphrase = fallback.getString(PASSPHRASE_KEY, null);
        if (fallbackPassphrase != null) return fallbackPassphrase;

        fallbackPassphrase = generatePassphrase();
        fallback.edit().putString(PASSPHRASE_KEY, fallbackPassphrase).commit();
        return fallbackPassphrase;
    }

    private String generatePassphrase() {
        byte[] bytes = new byte[32];
        new SecureRandom().nextBytes(bytes);
        StringBuilder result = new StringBuilder(64);
        for (byte value : bytes) result.append(String.format("%02x", value));
        return result.toString();
    }
}
