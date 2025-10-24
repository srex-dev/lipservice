module github.com/srex-dev/lipservice-go

go 1.21

require (
	github.com/google/uuid v1.4.0
	github.com/opentelemetry/opentelemetry-collector-contrib/pkg/translator/jaeger v0.88.0
	github.com/sirupsen/logrus v1.9.3
	go.opentelemetry.io/otel v1.21.0
	go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploggrpc v1.21.0
	go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp v1.21.0
	go.opentelemetry.io/otel/log v0.44.0
	go.opentelemetry.io/otel/sdk v1.21.0
	go.opentelemetry.io/proto/otlp v1.0.0
	google.golang.org/grpc v1.59.0
)

require (
	github.com/cenkalti/backoff/v4 v4.2.1 // indirect
	github.com/go-logr/logr v1.3.0 // indirect
	github.com/go-logr/stdr v1.2.2 // indirect
	github.com/golang/protobuf v1.5.3 // indirect
	github.com/grpc-ecosystem/grpc-gateway/v2 v2.18.1 // indirect
	go.opentelemetry.io/otel/metric v1.21.0 // indirect
	go.opentelemetry.io/otel/trace v1.21.0 // indirect
	golang.org/x/net v0.18.0 // indirect
	golang.org/x/sys v0.14.0 // indirect
	golang.org/x/text v0.14.0 // indirect
	google.golang.org/genproto/googleapis/api v0.0.0-20231120223509-83a465c0220f // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20231120223509-83a465c0220f // indirect
	google.golang.org/protobuf v1.31.0 // indirect
)
