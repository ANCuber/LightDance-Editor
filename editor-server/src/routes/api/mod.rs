//! REST API routes.

mod check_token;
mod create_user;
mod delete_user;
mod export_data;
mod export_logger;
mod get_dancer_fiber_data;
mod get_dancer_led_data;
mod login;
mod logout;
mod ping;
mod upload_data;

use axum::{
    extract::DefaultBodyLimit,
    routing::{get, post},
    Router,
};
use tower_http::trace::TraceLayer;

/// Build REST API routes for Axum server.
pub fn build_api_routes() -> Router {
    Router::new()
        .route("/checkToken", get(check_token::check_token))
        .route("/ping", get(ping::ping))
        .route("/login", post(login::login))
        .route("/logout", post(logout::logout))
        .route("/createUser", post(create_user::create_user))
        .route(
            "/getDancerFiberData",
            post(get_dancer_fiber_data::get_dancer_fiber_data),
        )
        .route(
            "/getDancerLEDData",
            post(get_dancer_led_data::get_dancer_led_data),
        )
        .route("/exportData", get(export_data::export_data))
        .route("/uploadData", post(upload_data::upload_data))
        .layer(DefaultBodyLimit::max(128 * 1000 * 1000))
        .layer(TraceLayer::new_for_http())
}
